**README**

# plant_classification

### Abstract
This project focuses on developing a system for the automated detection of poisonous plants using the YOLO11 model and describes the key aspects of the project structure, data acquisition and processing, and model deployment. The system is built upon an extensive dataset, derived from raw data provided by the Global Biodiversity Information Facility (GBIF) and specially prepared information on poisonous plants. Data collection is performed using a graphical user interface (GUI) implemented with the Kivy Framework, enabling user-friendly, targeted data gathering. The dataset is further expanded by data augmentation techniques such as Mixup and Mosaic, simulating real-world conditions for plant imagery.

At the core of the project lies a deep neural network approach, specifically YOLO11 in its “extra large” variant, pretrained on the COCO dataset. The parameter configuration incorporates different transformations and rotations to ensure robust plant detection under varied environmental settings. The training results are visualized through a custom GUI, making it easy to assess both the classification quality and bounding box predictions of the model.

An evaluation using mAP50–95 values indicates that the trained YOLO11 model, despite a comparatively small dataset, delivers high detection accuracy. This project thus contributes valuable insights into the practical implementation of automated detection methods and sets the stage for future applications and optimizations in automated image analysis.

---

## Table of Contents
1. [Getting Started](#getting-started)  
2. [Installation](#installation)  
3. [Running the Project](#running-the-project)  
4. [Contributing](#contributing)  
5. [License](#license)  

---

## Getting Started

Follow these guidelines to set up the project for development and testing on your local machine.

---

## Installation

1. **Clone this repository** (or download the ZIP file):
   ```bash
   git clone https://github.com/caesarakalaeii/plant_classification.git
   ```
2. **Navigate to the project directory**:
   ```bash
   cd plant_classification
   ```
3. **Install the required dependencies** using the `requirements.txt` file:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Project

**Data Collection**  
To start collecting data:
```bash
python data_collector.py
```

**Inference GUI**  
To launch the inference GUI:
```bash
python example_GUI.py
```

Adjust the above commands based on your specific setup or script names.

---

## Contributing

1. Fork the repository on GitHub.
2. Create a new feature branch (`git checkout -b feature/my-new-feature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push the branch (`git push origin feature/my-new-feature`).
5. Create a new Pull Request.

---

## License

This project is licensed under the [GNU Affero General Public License v3.0 (AGPLv3)](https://www.gnu.org/licenses/agpl-3.0.html).  