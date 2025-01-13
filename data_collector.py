import kivy
kivy.require('2.1.0')  # Adjust to your installed Kivy version
import pandas as pd
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from plant import download_gbif_images_with_pygbif

def get_column_from_toxic_plants(column_name):
    # Read the CSV, using semicolon as the separator
    df = pd.read_csv('./data_collector/data/toxic_plant_DataV2.csv', sep=';')

    # Extract the "Formal Botanical Name" column
    column = df[column_name]

    # Convert to a Python list (if you wish)
    column_values = column.tolist()

    return column_values

def get_formal_plant_names():
    return  get_column_from_toxic_plants('Formal Botanical Name')



class MultiSelectApp(App):
    def build(self):
        # Main layout
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # -----------------------
        # 1. Country (single selection via Spinner)
        # -----------------------
        main_layout.add_widget(Label(text='Select a Country (Code):'))

        # Replace with any country codes you need
        self.countries = ['DE', 'US', 'CA']
        self.country_spinner = Spinner(
            text='Select Country',
            values=self.countries,
            size_hint=(1, None),
            height=44
        )
        main_layout.add_widget(self.country_spinner)

        # -----------------------
        # 2. Plants (multi-selection via CheckBoxes)
        # -----------------------
        main_layout.add_widget(Label(text='Select Plants:'))

        # We'll store plant names and a reference to their CheckBox
        self.formal_plant_names = get_formal_plant_names()
        self.plant_checkboxes = {}

        # Use a scrollable layout in case you add many plants
        plant_scroll_view = ScrollView(size_hint=(1, None), size=(400, 100))
        plant_box = BoxLayout(orientation='vertical', size_hint_y=None)
        plant_box.bind(minimum_height=plant_box.setter('height'))

        for plant in self.formal_plant_names:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)

            label = Label(text=plant, size_hint_x=0.8)
            checkbox = CheckBox(size_hint_x=0.2)
            self.plant_checkboxes[plant] = checkbox

            row.add_widget(label)
            row.add_widget(checkbox)
            plant_box.add_widget(row)

        plant_scroll_view.add_widget(plant_box)
        main_layout.add_widget(plant_scroll_view)

        # -----------------------
        # 3. Months (multi-selection via CheckBoxes)
        # -----------------------
        main_layout.add_widget(Label(text='Select Months:'))

        self.month_names = [
            'January', 'February', 'March',
            'April', 'May', 'June',
            'July', 'August', 'September',
            'October', 'November', 'December'
        ]
        self.month_checkboxes = {}

        month_scroll_view = ScrollView(size_hint=(1, None), size=(400, 100))
        month_box = BoxLayout(orientation='vertical', size_hint_y=None)
        month_box.bind(minimum_height=month_box.setter('height'))

        for month in self.month_names:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)

            label = Label(text=month, size_hint_x=0.8)
            checkbox = CheckBox(size_hint_x=0.2)
            self.month_checkboxes[month] = checkbox

            row.add_widget(label)
            row.add_widget(checkbox)
            month_box.add_widget(row)

        month_scroll_view.add_widget(month_box)
        main_layout.add_widget(month_scroll_view)

        # -----------------------
        # 4. Slider: Number of Pictures
        # -----------------------
        slider_box = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, None), height=50)
        slider_box.add_widget(Label(text='Pictures:', size_hint_x=0.3))

        # This label will display the current slider value
        self.pictures_count_label = Label(text='0', size_hint_x=0.2)
        slider_box.add_widget(self.pictures_count_label)

        self.pictures_slider = Slider(
            min=0,
            max=500,
            value=10,  # default value
            size_hint_x=0.5
        )
        # Bind the slider value so that the label updates as we move the slider
        self.pictures_slider.bind(value=self.on_slider_value_change)
        slider_box.add_widget(self.pictures_slider)

        main_layout.add_widget(slider_box)

        # -----------------------
        # 5. Confirm Button
        # -----------------------
        confirm_button = Button(
            text='Confirm',
            size_hint=(1, None),
            height=44
        )
        confirm_button.bind(on_release=self.on_confirm)
        main_layout.add_widget(confirm_button)

        return main_layout

    def on_slider_value_change(self, slider, value):
        """Update the label text whenever the slider value changes."""
        self.pictures_count_label.text = str(int(value))

    def on_confirm(self, instance):
        # Country selection
        selected_country = self.country_spinner.text

        # Multiple plants (check which checkboxes are active)
        selected_plants = [
            plant for plant, checkbox in self.plant_checkboxes.items()
            if checkbox.active
        ]

        # Multiple months (check which checkboxes are active)
        selected_months = [
            month for month, checkbox in self.month_checkboxes.items()
            if checkbox.active
        ]
        months = []
        for selected_month in selected_months:
            month = self.month_names.index(selected_month) + 1
            months.append(month)
        # Read slider value
        pictures_to_download = int(self.pictures_slider.value)

        # Print the results (you can replace these prints with any custom logic)
        print("Country:", selected_country)
        print("Plants Selected:", selected_plants)
        print("Months Selected:", selected_months)
        print("Months:", months)
        print("Pictures to Download:", pictures_to_download)
        download_gbif_images_with_pygbif(selected_plants, pictures_to_download, country=selected_country, months=months)



if __name__ == '__main__':
    MultiSelectApp().run()
