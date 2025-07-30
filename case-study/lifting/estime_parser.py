
import json
from datetime import datetime
from rdflib import Namespace, Literal, RDF, URIRef
from rdflib.namespace import DCTERMS, DCAT, PROV

diva = Namespace("http://ns.inria.fr/diva/ontology#")
diva_th = Namespace("http://ns.inria.fr/diva/thesaurus#")

class LogParser:
    def __init__(self, json_data):
        self.json = json_data

    def convert_date(self, date_str):
        """Convert date string to ISO format"""
        dt = datetime.strptime(date_str, "%d/%m/%Y at %H:%M:%S")
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_action_time(self, index):
        """Extract the time from an event."""
        time = self.convert_date(self.json[index]['date'] )
        return time if time is not None else "unknown"
    
    def get_action_type(self, index):
        """Extract the action type from an event."""
        event = self.json[index]
        if event['eventInfo']['code'] == "create":
            return event['eventInfo']['item']
        else:
            return event['eventInfo']['code']

    def get_user(self):
        """Extract the user from an event."""
        event = self.json[0] # Assuming the first event contains user info
        if isinstance(event['parentName'], list):
            return event['parentName'][0].split('_').pop(-1).lower()  # Get last part after splitting the first item in the list
        else:
            return event['parentName'].split('_').pop(-1).lower()  # Get last part after splitting the string

    def get_step(self, index):
        """Extract the step from an event."""
        step = self.json[index]['index'] 
        return step if step is not None else index
    
    def get_view_metadata(self, index):
        parent_name = self.json[index]['parentName']
        if not isinstance(parent_name, list):
            event = self.json[index]
            window_value = self.get_window_value(event)
            parentName = event['parentName']
            view_type = "single" if "tableau" not in parentName.lower() else "dashboard"
            view_id = f"{view_type}_{event['parentIndex']}_{window_value}"
            
            return {
                'view_type': diva.SingleView if view_type == "single" else diva.DashboardView,
                'view_title': view_id,
                'view_description': f"View {view_id} with parent {parentName} and window {window_value}"
            }
        
        return None

    def get_dataset_year(self, dataset_name):
        if dataset_name == "grenoble":
            return "2010"
        elif dataset_name == "lyon":
            return "2015"
        elif dataset_name == "rennes":
            return "2018"
    
        return None
        

    def get_dataset_metadata(self, index):
        """Extract the dataset metadata from an event."""
        event_settings = self.json[index]['settings']

        metadata = {
            'location': event_settings.get('dataset', None),
            'spatialResolution': event_settings.get('partition', None),
            'issued': self.get_dataset_year(event_settings.get('dataset', None)),
            'creator': "CEREMA",
            'publisher': "ADISP",
            'accessURL': None,  # Placeholder for access URL
            'title': 'HTS ' + event_settings.get('dataset', None)
        }

        return metadata
    
    def get_window_value(self, event):
        # Default to 'cont_1' if window is None
        return event['window'] if event['window'] else 'cont_1'  

    def get_target_element_key(self, event):
        dataset_name = event['settings']['dataset']
        parent_name = event['parentName']
        dataset_partition = event['settings']['partition']
        return f"{dataset_name}-{parent_name}-{self.get_window_value(event)}-{dataset_partition}"

    # Define the mapping of visualization types to SKOS concepts
    def get_vis_type(self, vis_type, rep):
        
        vis_type_mapping = {
            'stacked-view': diva.StackedAreaGraph,
            'clock': diva.DonutChart,
            'chord-diagram': diva.ChordDiagram,
            'index': diva.StackedBarChart,
        }

        if vis_type == 'map':
            if rep == 'number':
                return diva.BubbleMap
            elif rep == 'ratio':
                return diva.ChoroplethMap
            else:
                return diva.Map

        elif vis_type == 'stc':
            return diva.STC

        return vis_type_mapping.get(vis_type, diva.UnknownVisualization)

    def get_remove_metadata(self, index):
        """Extract the metadata for a remove event."""
        event = self.json[index]
        metadata = {
            'action_type': diva_th.Delete,
            'manipulation_type': diva_th.Select,
            'ui_element': diva_th.Icon,
            'event_type': diva_th.Click,
            'title': "Delete Visualization",
            'description': f"Delete visualization of type {event['eventInfo']['value']}",
            'visualization': {
                "class": self.get_vis_type(event['eventInfo']['value'], None),
                "id": event['eventInfo']['value'],
                'title': event['eventInfo']['value'],
                'description': f"Visualization of type {event['eventInfo']['value']}",
            }
        }
        return metadata
    
    def get_field(self, eventInfo, element_details):
        field_name = eventInfo['item'] 
        if (eventInfo['item'] == 'sector'):  # spatial selection
            field_value = ', '.join(map(str, element_details.get('sectors', ['unknown']))) if isinstance(element_details.get('sectors'), list) else str(element_details.get('sectors', 'unknown'))
        elif (eventInfo['item'] == 'add'):  # add is an update of the indicator  
            field_name = 'indicator'
            field_value = element_details.get('indicator', 'unknown')
        else:
            field_value = eventInfo['value'] if 'value' in eventInfo else element_details.get(eventInfo['item'], 'unknown')

        return field_name, field_value
    
    def get_encodings(self, element_details):
        encodings = []

        indicator = element_details.get("indicator", None)
        category = element_details.get("category", None)
        period = element_details.get("period", None)
        sectors = element_details.get("sectors", None)

        depiction = element_details.get("depiction", None)

        if indicator:
            field = { "name": "indicator", "value": indicator, "type": diva_th.Categorical }
            
            channel = {}
            rep = element_details.get('rep', None)
            if depiction == 'map' and rep == "number":
                channel['concept'] = diva_th.Size
                channel['name'] = 'size'
            else: 
                channel['concept'] = diva_th.Color
                channel['name'] = 'color'

            custom_elements = element_details.get('customize', [])

            encodings.append({ "field": field, "channel": channel, 'legend': 'legend' in custom_elements})

        if category:
            field = {
                "name": "category", 
                "value": category, 
                "type": diva_th.Categorical, 
            }

            channel = {
                "concept": diva_th.Color, 
                "name": 'color',
            }

            encodings.append({ 'field': field, 'channel': channel, 'legend': None })
        
        if period:
            time = element_details.get("time", None)
            field = {
                "name": "period", 
                "value": period if time == 'individual' else None,
                "type": diva_th.Temporal, 
            }
        
            channel = {}
            if depiction in ['index', 'stacked-view']:
                channel['concept'] = diva_th.X
                channel['name']= 'x'
            elif depiction == 'STC':
                channel['concept'] = diva_th.Z 
                channel['name'] = 'z'
            elif depiction == 'clock':
                channel['name'] = 'theta'
                channel['concept'] = diva_th.Theta
            else: # map and chord diagram do not encode temporal information
                channel['name'] = None
                

            encodings.append({ "field": field, "channel": channel, 'legend': None })

        if sectors:
            field = { "name": "sectors", "type": diva_th.Categorical }

            space = element_details.get("space", None)
            if space == "individual":
                field['value'] = ', '.join(map(str, sectors)) if isinstance(sectors, list) else str(sectors)
            else:
                field['value'] = None

            # Determine the channel according to the visualization type                
            channel = {}
            if depiction in ['map', 'STC']:
                channel['concept'] = diva_th.Polygon
                channel['name'] = 'polygon'
            elif depiction == 'chord-diagram':
                channel['concept'] = diva_th.Theta
                channel['name'] = 'theta'
            else:
                channel['name'] = None
                
            encodings.append({ "field": field, "channel": channel, 'legend': None})

        return encodings
    

    def get_signals(self, element_details):
        signals = []

        spatial_granularity = element_details.get('space', None)
        temporal_granularity = element_details.get('time', None)
        aggregation = element_details.get('rep', None)
        ftime = element_details.get('ftime', None)
        fspace = element_details.get('fspace', None)
        fzoom =  element_details.get('fzoom', None)

        depiction = element_details.get('depiction', None)

        if spatial_granularity:
            signals.append({ "id": 'space',  "type": diva_th.DataAggregation, "label": "Spatial Granularity", "value": spatial_granularity })

        if temporal_granularity:
            signals.append({ "id": "time", "type": diva_th.DataAggregation, "label": "Temporal Granularity", "value": temporal_granularity})

        if aggregation:
            signals.append({ "id": "rep", "type": diva_th.DataAggregation, "label": "Metric transform for map-represented data", "value": aggregation})

        if ftime:
            signals.append({ "id": "ftime", "type": diva_th.LockAnimation, "label": "Lock Time Animation", "value": ftime})

        if fspace:
            signals.append({ "id": "fspace", "type": diva_th.LockBrushing, "label": "Lock Spatial Brushing", "value": fspace})

        if fzoom:
            signals.append({ "id": "fzoom", "type": diva_th.LockZoom, "label": "Lock Zoom", "value": fzoom })

        if depiction == 'map' or depiction == 'stc':
            signals.append({ "id": "display", "type": diva_th.Display, "label": "Display Visualization", "value": True})

        return signals

    
    def get_visualization_metadata(self, element_details):

        vis_type = element_details.get('depiction', None)
        
        metadata = {
            "class": self.get_vis_type(vis_type, element_details['rep']),
            "id": vis_type,
            "title": element_details['label'],
            'description': f"Visualization of type {vis_type}",
            'encodings': self.get_encodings(element_details), 
            'signals': self.get_signals(element_details)
        }

        return metadata
    
    def get_UI_elements(self, element_details):
        metadata = []
        for element in element_details.get('customize', []):
            ui_element = self.get_UI_Element(element)
            if ui_element:
                metadata.append(ui_element)

        return metadata

    def get_add_vis_metadata(self, index):
        """Extract the metadata for an add event."""
        event = self.json[index]
        target_element_key = self.get_target_element_key(event)
        element_details = event['settings']['elements'].get(target_element_key, None)
        
        vis_type = element_details['depiction']
        
        metadata = {
            'action_type': diva_th.Produce,
            'manipulation_type': diva_th.Select,
            'ui_element': diva_th.DropdownButton,
            'event_type': diva_th.Click,
            'title': "Add Visualization",
            'description': f"Add visualization of type {vis_type}",
            'visualization': self.get_visualization_metadata(element_details),
            'view_ui_elements': self.get_UI_elements(element_details)
        }
            
        return metadata

    def get_switch_metadata(self, index):
        """Extract the metadata for a switch event."""
        event = self.json[index]
        
        vis_type = event['eventInfo']['value']
        from_vis_type = 'map' if vis_type == 'stc' else 'stc'
        metadata = {
            'action_type': diva_th.Browse,
            'manipulation_type': diva_th.Switch,
            'ui_element': diva_th.ToggleSwitch,
            'event_type': diva_th.Click,
            'title': "Switch Visualization",
            'description': f"Switching from {from_vis_type} to {vis_type}",
            'visualization': {
                "class": self.get_vis_type(vis_type, None),
                "id": vis_type,
                "title": vis_type,
                'description': f"Visualization of type {vis_type}",
                'signals': [{'id': 'display', 'type': diva_th.Display, 'label': 'Display Visualization', 'value': True}]
            }
        }

        target_element_key = self.get_target_element_key(event)
        element_details = event['settings']['elements'].get(target_element_key, None)
        if element_details: # if there is data on the visualization, then use it
            metadata['visualization'] = self.get_visualization_metadata(element_details)
            metadata['view_ui_elements']= self.get_UI_elements(element_details)
        
        return metadata
    

    def get_global_metadata(self, index):
        """Extract the metadata for a global event. It is a switch of datasets."""
        dataset = self.get_dataset_metadata(index)
        metadata = {
            'action_type': diva_th.Import,
            'manipulation_type': diva_th.Switch,
            'ui_element': diva_th.DropdownButton,
            'event_type': diva_th.Click,
            'title': "Dataset Import",
            'description': f"Import dataset: {dataset['location']} with resolution {dataset['spatialResolution']}",
            'dataset': dataset,
        }
        return metadata
    
    def get_transform_type(self, field_name, rep):
        """Extract the action type for a modify event."""
        if field_name in ['sector', 'typology', 'indicator']:
            return diva_th.Filter
        elif field_name in ['time', 'space']:
            return diva_th.Granularity
        elif field_name in ['rep']:
            return diva_th.MetricTransform
        else:
            return diva_th.Transform
        
    def get_UI_Element(self, value):
        """Get the UI element type based on the value."""
        if value == 'details':
            return diva_th.DetailsView
        elif value == 'legend':
            return diva.Legend
        elif value == 'labels':
            return diva_th.Label
        
        return None

    def get_modify_action(self, eventInfo):
        item = eventInfo.get('item', None)
        value = eventInfo.get('value', None)
        
        if item == 'customize':
            return diva_th.DetailsOnDemand if value else diva_th.Delete, self.get_UI_Element(eventInfo.get('dimension', None))
        elif item == 'details':
            return diva_th.DetailsOnDemand if value else diva_th.Delete, diva_th.DetailsView
        elif item == 'filtering':
            return diva_th.Filter, None
        
        return None, None
      

    def get_modify_metadata(self, index):
        """Extract the metadata for a modify event."""
        event = self.json[index]

        metadata = {
            'action_type': None,  # Will be determined later
            'manipulation_type': diva_th.Select, # There is always a selection, either directly on the visualization or through a button
            'ui_element': None,  # Will be determined later
            'event_type': diva_th.Click,
        }

        target_element_key = self.get_target_element_key(event)
        element_details = event['settings']['elements'].get(target_element_key, None)
    
        action_type, vis_ui_element = self.get_modify_action(event['eventInfo'])
        if action_type is not None:
            metadata['title'] = "Display UI Element"
            metadata['description'] = f"Display UI Element"
            metadata['ui_element'] = vis_ui_element
        elif action_type is None and element_details is not None:
            field_name, field_value = self.get_field(event['eventInfo'], element_details) # used to describe the transform action
            
            action_type = self.get_transform_type(field_name, element_details.get('rep', None))
            metadata['manipulation_type'] = diva_th.Select

            is_sector = event['eventInfo'].get('item', None) == 'sector'
            if not is_sector:
                metadata['ui_element'] = diva_th.DropdownButton    
            
            metadata['title'] = "Transform Visualization"
            metadata['description'] = f"Transform visualization by modifying {field_name} to {field_value}"
        
        if action_type is None and element_details is None:
            return None

        metadata['action_type'] = action_type

        if element_details is not None:
            metadata['visualization'] = self.get_visualization_metadata(element_details)
            metadata['view_ui_elements']= self.get_UI_elements(element_details)
    
        return metadata
    