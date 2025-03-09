from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle, Ellipse
from ultralytics import YOLO
import os
# import pygame
# still some bugs with displaying multibe confidience Score values -> example start app and load Digitalis_L_29.jpeg
# missing feature: Displaying the detected plant with the highest confidience score ~
#                  swaping between BOundary boxes and Confidence scores of plants via toggle button ADDED
#                  cool sound effect when loading a picture ADDED
class ModelPathSelector(Popup):
    def __init__(self, app, **kwargs):
        super().__init__(title='Select a YOLO Model', size_hint=(0.9, 0.9), **kwargs)
        self.app = app
        
        layout = BoxLayout(orientation='vertical')
        self.filechooser = FileChooserIconView(path=os.getcwd(), dirselect=True)
        layout.add_widget(self.filechooser)
        
        btn_select = Button(text='Select Folder', size_hint_y=None, height=50)
        btn_select.bind(on_press=self.select_model_path)
        layout.add_widget(btn_select)
        
        self.content = layout
    
    def select_model_path(self, instance):
        if self.filechooser.selection:
            self.app.selected_model_path = self.filechooser.selection[0]
            self.dismiss()
            self.app.start_main_app()

class ImageViewer(BoxLayout):
    def __init__(self,selected_model_path, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        # Add canvas to main layout
        self.image = Image()
        self.add_widget(self.image)

        button_layout = GridLayout(cols=2, size_hint_y=None, height=50)

        self.btn_load = Button(text='Load Image', size_hint_y=None, height=50)
        self.btn_load.bind(on_press=self.show_filechooser)
        button_layout.add_widget(self.btn_load)

        # Add Togglebutton for Boundingbox & Conf
        self.toggle_bbox_conf = ToggleButton(text='Show Bounding Boxes & Confidence', state='normal', size_hint_y=None, height=50)
        self.toggle_bbox_conf.bind(on_press=self.toggle_bounding_boxes_confidence)
        button_layout.add_widget(self.toggle_bbox_conf)
        
        # Three-Stage Button with Text Fields
        # self.stage_button = Button(text="all plants")
        # self.stage_button.bind(on_press=self.next_stage)
        # button_layout.add_widget(self.stage_button)

        # Sound Button
        # self.sound_button = ToggleButton(text='Enable Sound', state='normal', size_hint_y=None, height=50)
        # self.sound_button.bind(on_press=self.toggle_sound)
        # button_layout.add_widget(self.sound_button)

        self.add_widget(button_layout)

        # Create a BoxLayout to hold the radio-style buttons
        stage_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)

        # "Radio Buttons" using ToggleButton with a common group
        self.stage_col = ToggleButton(text="Colchicum autumnale L", group="stages", state="down")
        self.stage_digi = ToggleButton(text="Digitalis L", group="stages")
        self.stage_jaco = ToggleButton(text="Jacobaea vulgaris", group="stages")
        self.stage_all = ToggleButton(text="All plants", group="stages")

        # Bind buttons
        self.stage_col.bind(on_press=self.next_stage)
        self.stage_digi.bind(on_press=self.next_stage)
        self.stage_jaco.bind(on_press=self.next_stage)
        self.stage_all.bind(on_press=self.next_stage)

        # Add buttons to layout
        stage_layout.add_widget(self.stage_col)
        stage_layout.add_widget(self.stage_digi)
        stage_layout.add_widget(self.stage_jaco)
        stage_layout.add_widget(self.stage_all)
        # Add to main layout
        self.add_widget(stage_layout)
        # setting local Variables
        self.selected_model_path = selected_model_path
        self.plant_name_list = {0: "Colchicum autumnale L", 1: "Digitalis L", 2: "Jacobaea vulgaris"}
        self.color_table = {0: (0, 0.2, 0.69, 1) , 1: (1, 0, 0, 1) , 2: (0, 0, 0.69, 1) }
        self.show_bboxes_conf = False
        self.sound_on = False
        self.radio_button_pressed = "Colchicum autumnale L"
        self.yolo_model = YOLO(self.convert_path())  # Pfad für das YOlo Modell
        #pygame.mixer.init()
        #pygame.mixer.music.load("Soundfiles/magic-3-278824.mp3")

    def show_filechooser(self, instance):
        filechooser = FileChooserIconView(path=os.getcwd())
        filechooser.bind(on_submit=self.load_image)
        popup = Popup(title='Select Image', content=filechooser, size_hint=(1, 1))
        popup.open()
        self.popup = popup

    def next_stage(self, instance):
        if self.stage_col.state == "down":
            self.radio_button_pressed = "Colchicum autumnale L"
        elif self.stage_jaco.state == "down":
            self.radio_button_pressed = "Jacobaea vulgaris"
        elif self.stage_digi.state == "down":
            self.radio_button_pressed = "Digitalis L"
        elif self.stage_all.state == "down":
            self.radio_button_pressed = "All plants"
        else:
            self.radio_button_pressed = "none"
        if self.show_bboxes_conf:
            self.draw_bounding_boxes(self.image.source)
    """ Old function of the Multistage button
        if self.stage_button.text == "Colchicum autumnale L":
            self.stage_button.text = "Digitalis L"
        elif self.stage_button.text == "Digitalis L":
            self.stage_button.text = "Jacobaea vulgaris"
        elif self.stage_button.text == "Jacobaea vulgaris":
            self.stage_button.text = "all plants"
        else:
            self.stage_button.text = "Colchicum autumnale L"
    """

    def load_image(self, filechooser, selection, *args):
        if selection:
            self.image.source = selection[0]
            self.image.reload()
            if self.show_bboxes_conf:
                self.draw_bounding_boxes(selection[0])
        self.popup.dismiss()
    
    def toggle_bounding_boxes_confidence(self, instance):
        self.show_bboxes_conf = instance.state == 'down'
        if self.image.source:
            self.draw_bounding_boxes(self.image.source)
        else:
            self.image.canvas.after.clear()
    
    def toggle_sound(self, instance):
        self.sound_on = instance.state == 'down'

    def draw_bounding_boxes(self, image_path):
        results = self.yolo_model(image_path)
        orig_y, orig_x =results[0].orig_shape
        img_scale_factor =  (self.image.height) / orig_y
        black_bars_width = self.image.width - self.image.height * self.image.image_ratio
        self.image.canvas.after.clear()
        #self.draw_image_corners()
        if self.show_bboxes_conf:
            with self.image.canvas.after:
                for result in results:
                    for box, conf, size, plant_detected in zip(result.boxes.xyxy, result.boxes.conf,result.boxes.xywh, result.boxes.cls):
                        Color(*self.color_table[plant_detected.item()])
                        x1, y1, x2, y2 = map(int, box[:4])
                        b, a, width, height = map(int, size[:4])
                        if self.radio_button_pressed == "none":
                            print("No Radio Button is pressed")
                        elif self.plant_name_list[plant_detected.item()] == self.radio_button_pressed:
                            # Vorsicht basis darstellung des Images self.image.width = 800 self.image.height = 500 da die beiden buttons jeweils 50 pixel groß sind
                            Line(rectangle=(x1*img_scale_factor+black_bars_width/2,y1*img_scale_factor+100,width*img_scale_factor,height*img_scale_factor), width = 2) #x1, y1, x2, y2
                            Label(text=f'{conf:.2f}',outline_width=2, pos=(x1*img_scale_factor+black_bars_width/2, y2*img_scale_factor+40))
                        elif self.radio_button_pressed == 'All plants':
                            Line(rectangle=(x1*img_scale_factor+black_bars_width/2,y1*img_scale_factor+100,width*img_scale_factor,height*img_scale_factor), width = 2) #x1, y1, x2, y2
                            Label(text=f'{conf:.2f}',outline_width=2, pos=(x1*img_scale_factor+black_bars_width/2, y2*img_scale_factor+40))
                        # extra for the sound button
                        # if conf > 0.8 and self.sound_on:
                        #    pygame.mixer.music.play()
    def draw_image_corners(self):
        with self.image.canvas.after:
            Color(0, 1, 0, 1)  # Green corner markers
            size = 10  # Size of the marker
            width, height = self.image.texture_size
            img_scale_factor =  (self.image.height) / height
            width_shown_img = self.image.width- img_scale_factor*self.image.width
            corner_positions = [(self.image.width, self.image.height), (200, self.image.height+95), (0, height - size), (width - size, height - size)]
            for x, y in corner_positions:
                Ellipse(pos=(x, y), size=(size, size))

    def convert_path(self):
        return_path = self.selected_model_path.replace(os.getcwd()+"\\","")
        return return_path.replace("\\","/")
    
class ImageApp(App):
    def build(self):
        self.selected_model_path = None
        self.path_selector = ModelPathSelector(self)
        self.path_selector.open()
        return BoxLayout()
    
    def start_main_app(self):
        self.root.clear_widgets()
        self.root.add_widget(ImageViewer(self.selected_model_path))
if __name__ == '__main__':
    ImageApp().run()

