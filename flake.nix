{
  # Keep this line accurate and one line long: `nix flake metadata` prints it,
  # and it is the first thing a cold agent learns about the repo.
  description = "plant_classification -- YOLO11 poisonous-plant detector with Kivy data-collection and inference GUIs. Run `nix flake show` for the command map.";

  # nixpkgs is the only input, on purpose.
  #
  # flake-utils would buy exactly one thing here -- eachDefaultSystem -- which is
  # the three-line genAttrs below. In exchange it costs a second lock node in
  # every repo (flake-utils transitively pulls `systems`), a second upstream that
  # can break, and a hardcoded system list this repo cannot edit. That list is
  # currently broken: it still contains x86_64-darwin, which now throws (see
  # `systems` below).
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    # `...` rather than a closed { self, nixpkgs }: adding a second input later
    # would otherwise fail with "called with unexpected argument 'self'".
    { nixpkgs, ... }:
    let
      lib = nixpkgs.lib;

      # x86_64-darwin is deliberately absent. nixpkgs 26.11 replaced that whole
      # attribute set with `throw "Nixpkgs 26.11 has dropped support for
      # x86_64-darwin"`. genAttrs is lazy, so plain `nix develop` on Linux would
      # not notice -- it detonates later, on `nix flake check --all-systems`.
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];

      # Stand-in for flake-utils.lib.eachDefaultSystem. Passes `pkgs` rather than
      # a system string, because that is what every call site below wants.
      forAllSystems = f: lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});

      # ======================================================================
      # PER-REPO BLOCK 1 -- the toolchain
      # ======================================================================
      # requirements.txt is unpinned (requests, pygbif, ultralytics, docutils,
      # Kivy, pandas), so nix owns the interpreter and the launcher while uv owns
      # the wheels -- see `setup`. There is no CI workflow, no Dockerfile and no
      # .python-version in this repo, so nothing upstream pins a Python version;
      # 3.13 is the newest release every one of those six projects ships wheels
      # for. Pinned by major on purpose: `python3` moves under you and every
      # existing .venv in the fleet stops matching on the same afternoon.
      #
      # GPU IS OUT OF SCOPE. ultralytics pulls torch, and the default PyPI torch
      # wheel drags ~3 GB of bundled CUDA libraries that are useless without a
      # matching host driver, so UV_TORCH_BACKEND below forces the CPU index.
      # Nothing here is CUDA-aware; training on CPU works but is slow. Do not
      # "fix" that with pkgs.cudaPackages -- adding CUDA to a template is a
      # multi-gigabyte closure for the one machine that could use it.
      toolchain =
        pkgs:
        [
          # ---- this repo's ecosystem ----
          pkgs.python313
          pkgs.uv
          pkgs.ruff

          # ---- present in every repo in the fleet ----
          pkgs.git
          pkgs.jq
          pkgs.gnumake
        ]
        # Both entrypoints (data_collector.py, example_GUI.py) are Kivy apps, so
        # the only `run` this repo has needs an X display. xvfb-run gives a
        # headless agent one (`nix develop -c xvfb-run dev-run`) for ~150 MB,
        # which is the reason it is worth its closure here and nowhere else.
        # It supplies a DISPLAY, not a GL driver -- see nativeLibs.
        ++ lib.optionals pkgs.stdenv.hostPlatform.isLinux [ pkgs.xvfb-run ];

      # ======================================================================
      # PER-REPO BLOCK 2 -- libraries that get dlopened, not linked
      # ======================================================================
      # manylinux wheels carry .so files that are dlopened at runtime, so neither
      # patchelf nor the nix linker ever sees them and NixOS has no /usr/lib for
      # them to find. LD_LIBRARY_PATH is a blunt instrument, so this list is the
      # minimum that survived a leave-one-out test -- drop any of the first five
      # and a named import dies:
      #   stdenv.cc.cc.lib  libstdc++.so.6        -- numpy
      #   zlib              libz.so.1             -- numpy, and Kivy's SDL2 per ldd
      #   libGL             libGL.so.1            -- cv2, via ultralytics
      #   glib              libgthread-2.0.so.0   -- cv2
      #   libxcb            libxcb.so.1           -- cv2
      # mtdev is the one entry that is not strictly required: Kivy degrades
      # without it, but its multitouch probe then prints a bare
      # `OSError: libmtdev.so.1: cannot open shared object file` traceback on
      # every GUI start, which is exactly the noise an agent misreads as a crash.
      #
      # The X11 client libraries are deliberately NOT here even though Kivy's
      # SDL2 dlopens them: they arrive transitively through libglvnd's own
      # DT_RUNPATH, verified by a Kivy window opening with every libx*/libxcursor
      # entry stripped from the path. Do not "fix" that by adding them back.
      # If you ever do need one, use the top-level `libx11`/`libxrandr` attrs and
      # NOT `pkgs.xorg.libX11`: the whole `xorg` set is deprecated on this pin and
      # each reference prints an "evaluation warning" on every nix invocation,
      # which is per-call noise in an agent's captured output.
      #
      # Linux-only by construction. Do NOT guard these with `pkgs ? libGL`
      # instead: on darwin the attribute exists and is `null`, so a presence
      # check passes and then `.name` fails with "expected a set but found null".
      #
      # HONEST LIMIT: this makes the GL *loader* resolvable, not GL itself.
      # pkgs.libGL is libglvnd, a dispatch library; the real libGLX_mesa comes
      # from the host (/run/opengl-driver/lib on NixOS). Imports therefore work
      # anywhere, while actually opening a window needs host graphics config that
      # no project flake can supply. A green GUI launch on a workstation does not
      # prove this shell is self-contained.
      nativeLibs =
        pkgs:
        lib.optionals pkgs.stdenv.hostPlatform.isLinux [
          pkgs.stdenv.cc.cc.lib
          pkgs.zlib
          pkgs.libGL
          pkgs.glib
          pkgs.libxcb
          pkgs.mtdev
        ];

      # ======================================================================
      # PER-REPO BLOCK 3 -- constant environment variables
      # ======================================================================
      # Only constants belong here. Anything that must READ an existing value
      # (LD_LIBRARY_PATH), UNSET something (SOURCE_DATE_EPOCH) or touch the work
      # tree goes in the shellHook further down.
      #
      # Applied to BOTH surfaces -- the dev shell and every `nix run` wrapper --
      # so a command cannot behave differently depending on how it was invoked.
      envVars = pkgs: {
        # Keep uv on the nix interpreter. Left alone it downloads its own
        # portable CPython, which then resolves a different set of wheels than
        # this shell pins: two Pythons, one venv, no way to tell which is live.
        UV_PYTHON = "${pkgs.python313}/bin/python";
        UV_PYTHON_DOWNLOADS = "never";
        # /nix/store and the work tree are usually different filesystems, so
        # uv's default hardlink strategy warns on every single install.
        UV_LINK_MODE = "copy";
        PIP_DISABLE_PIP_VERSION_CHECK = "1";

        # The whole GPU decision, in one variable: uv resolves torch and friends
        # against download.pytorch.org/whl/cpu instead of PyPI's CUDA-bundled
        # default. ~250 MB rather than ~3 GB, and no driver/toolkit version to
        # match. Set it to a cu* value in a throwaway venv if you ever need GPU;
        # do not commit that here.
        UV_TORCH_BACKEND = "cpu";

        # Kivy parses sys.argv itself and errors on flags it does not recognise,
        # which would make `nix run .#run -- anything` fail before the app
        # starts. This hands argv to the script instead.
        KIVY_NO_ARGS = "1";
      };

      # ======================================================================
      # PER-REPO BLOCK 4 -- the command map
      # ======================================================================
      # THE single source of truth. It generates `apps` (so `nix run .#run`
      # works), the `dev-*` wrappers on PATH inside the shell, and `dev-help`.
      # Nothing is written twice, so `nix flake show` can never disagree with
      # what `dev-run` actually runs.
      #
      # `test` is deliberately absent: this repo has no test suite, no pytest
      # config and no tests/ directory. Absence is information -- a stub that
      # echoed "no tests" would turn the command map into a liar.
      commands = pkgs: {
        setup = {
          description = "(network) create .venv from requirements.txt (CPU torch, ~1.5 GB)";
          text = ''
            uv venv "$REPO_ROOT/.venv"
            uv pip install --python "$REPO_ROOT/.venv/bin/python" -r "$REPO_ROOT/requirements.txt"
          '';
        };
        build = {
          # This is the artifact the repo exists to produce. train.py reads
          # "model/yolo11x.pt" and "data/plant classification/data.yaml" as paths
          # relative to its own directory, hence the cd -- the dataset (288 train
          # / 96 val images) is committed, the pretrained checkpoint is gitignored
          # and ultralytics fetches it on first run.
          #
          # NOT HERMETIC, and in a way that bites across repos: ultralytics keeps
          # a persistent ~/.config/Ultralytics/settings.json and pins runs_dir /
          # datasets_dir there from whatever directory it was FIRST imported in.
          # So output may land somewhere other than this repo. Check that file
          # before believing a path, and do not try to fix it from the flake --
          # a hardcoded YOLO_CONFIG_DIR here would just move the problem.
          description = "(network) train the YOLO11 detector -- 300 epochs, many hours on CPU";
          text = ''
            cd "$REPO_ROOT/training"
            "$REPO_ROOT/.venv/bin/python" train.py "$@"
          '';
        };
        lint = {
          description = "ruff check (reports pre-existing findings in this repo)";
          text = ''ruff check "$@"'';
        };
        fmt = {
          description = "ruff format (rewrites files)";
          text = ''ruff format "$@"'';
        };
        run = {
          # The venv interpreter by absolute path, not a bare `python`. The
          # wrappers prepend the nix toolchain to PATH, so a bare name would
          # resolve to the store copy and miss every dependency `setup`
          # installed. Same reason the script is named absolutely: `nix run` and
          # `nix develop` both start in the caller's directory.
          description = "launch the Kivy inference GUI (needs a display; try xvfb-run when headless)";
          text = ''"$REPO_ROOT/.venv/bin/python" "$REPO_ROOT/example_GUI.py" "$@"'';
        };
      };

      # ======================================================================
      # GENERIC MACHINERY -- identical in every repo in this fleet, do not edit
      # ======================================================================

      # Prepend, never assign: a host LD_LIBRARY_PATH may be carrying something
      # the user needs, and clobbering it breaks binaries they launch from here.
      # Linux only -- on darwin the loader variable is DYLD_*, and exporting a
      # Linux-shaped value there is at best useless.
      ldPreamble =
        pkgs:
        lib.optionalString (pkgs.stdenv.hostPlatform.isLinux && nativeLibs pkgs != [ ]) ''
          export LD_LIBRARY_PATH="${lib.makeLibraryPath (nativeLibs pkgs)}''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
        '';

      # Every command gets $REPO_ROOT. `nix run` and `nix develop` both start in
      # whatever directory they were invoked from, so a bare `.venv` silently
      # forks a second environment as soon as an agent works from a subdirectory.
      # Note we do NOT cd there: commands act on the caller's cwd on purpose.
      rootPreamble = ''
        REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
        export REPO_ROOT
      '';

      # One derivation per command, reused by both `apps` and the dev shell, so
      # the two can never diverge. `dev-` prefixed because a bare `test` binary
      # earlier on PATH would shadow the POSIX shell builtin and quietly break
      # every script in the repo that uses it.
      wrappers =
        pkgs:
        lib.mapAttrs (
          name: cmd:
          pkgs.writeShellApplication {
            name = "dev-${name}";
            runtimeInputs = toolchain pkgs;
            runtimeEnv = envVars pkgs;
            meta.description = cmd.description;
            text = ''
              ${rootPreamble}
              ${ldPreamble pkgs}
              ${cmd.text}
            '';
          }
        ) (commands pkgs);

      helpFor =
        pkgs:
        let
          cmds = commands pkgs;
          names = lib.attrNames cmds;
          width = lib.foldl' (a: n: lib.max a (builtins.stringLength n)) 0 names;
          pad = n: n + lib.concatStrings (lib.genList (_: " ") (width - builtins.stringLength n));
          line = n: c: "  dev-${pad n}  ${c.description}";
        in
        pkgs.writeShellApplication {
          name = "dev-help";
          meta.description = "print this repo's command map (works offline)";
          text = ''
            cat <<'EOF'
            ${lib.concatStringsSep "\n" (lib.mapAttrsToList line cmds)}
            EOF
          '';
        };
    in
    {
      # `nix flake show` -- the discovery entrypoint, and deliberately the whole
      # machine-facing contract: every app carries a meta.description, which
      # `nix flake show` prints inline and `nix flake show --json` exposes at
      # .apps.<system>.<name>.description. Pure evaluation, so an agent gets the
      # entire command map in one cheap call without reading a README.
      apps = forAllSystems (
        pkgs:
        lib.mapAttrs (name: cmd: {
          type = "app";
          program = "${(wrappers pkgs).${name}}/bin/dev-${name}";
          meta.description = cmd.description;
        }) (commands pkgs)
      );

      # `nix develop` -- the toolchain, plus a dev-<verb> for every app.
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = toolchain pkgs ++ lib.attrValues (wrappers pkgs) ++ [ (helpFor pkgs) ];

          env = envVars pkgs;

          # Some C extensions compile at -O0, where glibc's _FORTIFY_SOURCE
          # becomes a hard error instead of a warning.
          hardeningDisable = [ "fortify" ];

          shellHook = ''
            # mkShell inherits SOURCE_DATE_EPOCH=315532800 (1980-01-01) from
            # stdenv, and any wheel or zip built in here then dies with "ZIP does
            # not support timestamps before 1980".
            unset SOURCE_DATE_EPOCH

            ${rootPreamble}
            ${ldPreamble pkgs}

            # Nothing networked, nothing stateful and nothing interactive above
            # this line, and nothing below it either. No venv creation, no
            # `uv pip install`, no model download. Bootstrapping in the hook
            # makes a cold `nix develop -c ...` start downloading before it runs
            # anything, on EVERY invocation -- the exact failure an unattended
            # agent cannot diagnose. That is what `dev-setup` is for.

            # The banner is interactive-only, and this guard is load-bearing:
            # shellHook output lands on the STDOUT of `nix develop -c <cmd>`, so
            # an unguarded echo corrupts anything parsing it. $- is the only
            # reliable discriminator -- it lacks `i` for `nix develop -c` and has
            # it at an interactive prompt. Do not test $PS1 (unset in both) or
            # $IN_NIX_SHELL (set in both), and do not use `[ -t 1 ]`: that still
            # passes when an agent harness allocates a pty. >&2 is layer two.
            case $- in
              *i*) echo "plant_classification dev shell -- 'dev-help' for the command map" >&2 ;;
            esac
          '';
        };
      });

      # `nix flake check` -- honest by construction. It realises the toolchain
      # closure (so a typo'd or currently-broken attr fails here) and builds
      # every wrapper, which runs shellcheck over every command text. NEVER add a
      # check that always passes: an agent reads "all checks passed!" as a
      # signal, and a fake check makes `nix flake check` a liar.
      checks = forAllSystems (pkgs: {
        toolchain =
          pkgs.runCommand "toolchain-check"
            {
              nativeBuildInputs = toolchain pkgs ++ lib.attrValues (wrappers pkgs);
            }
            ''
              for verb in ${lib.escapeShellArgs (lib.attrNames (commands pkgs))}; do
                command -v "dev-$verb" > /dev/null || {
                  echo "dev-$verb is not on PATH" >&2
                  exit 1
                }
              done
              touch "$out"
            '';
      });

      # `nix fmt` -- formats the *Nix* in this repo; project code is `dev-fmt`.
      # nixfmt-tree (the treefmt wrapper) rather than bare nixfmt, because bare
      # nixfmt tries to parse every path handed to it and fails on non-Nix files.
      formatter = forAllSystems (pkgs: pkgs.nixfmt-tree);
    };
}
