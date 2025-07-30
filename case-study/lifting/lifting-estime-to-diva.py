from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, PROV, XSD, DCTERMS, FOAF, DCAT, RDFS

import json
import sys
import os
import traceback

from estime_parser import LogParser

diva = Namespace("http://ns.inria.fr/diva/ontology#")
diva_th = Namespace("http://ns.inria.fr/diva/thesaurus#")  # Thesaurus
diva_d = Namespace("http://ns.inria.fr/diva/data#")

# Create the rdf:_i property dynamically
rdf_ns = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

def get_event_suffix(user_name, event_type, event_id):
    """Generate a unique URI suffix based on user name, event type, and event ID."""
    return f"{user_name}_{event_type}_{event_id}"

def get_entity_suffix(user_name):
    """Generate a stable URI suffix based on user name and event type."""
    # Use a hash to ensure the suffix is stable and unique
    return f"{user_name}"

def get_field_uri(field_name, field_value):
    """Generate a stable URI for a field based on its name and value."""
    # Use a hash to ensure the URI is stable and unique
    sanitized_field_name = field_name.replace("-", "_").replace(" ", "_").replace(".", "")
    sanitized_field_value = field_value if not isinstance(field_value, str) else field_value.replace("-", "_").replace(" ", "_").replace(".", "")
    return URIRef(f"{diva_d}field_{sanitized_field_name}_{sanitized_field_value}")

def get_signal_uri(dimension, value):
    """Generate a stable URI based on signal dimension and value."""
    # Use a hash to ensure the suffix is stable and unique
    return URIRef(f"{diva_d}signal_{dimension}_{value}")

def get_encoding_uri(field_name, field_value, channel):
    """Generate a stable URI for an encoding based on field name, value, and channel."""
    
    # Use a hash to ensure the URI is stable and unique
    sanitized_field_name = field_name.replace("-", "_").replace(" ", "_").replace(".", "")
    parts = [ sanitized_field_name ]

    if field_value is not None:
        sanitized_field_value = field_value if not isinstance(field_value, str) else field_value.replace("-", "_").replace(" ", "_").replace(".", "")
        parts.append(str(sanitized_field_value))

    if channel is not None: 
        sanitized_channel = channel.replace("-", "_").replace(" ", "_").replace(".", "")
        parts.append(sanitized_channel)

    return URIRef(f"{diva_d}encoding_{'_'.join(parts)}")

def get_vis_uri(vis_type, uri_suffix):
    vis_id = f"{vis_type.replace('-', '')}"
    vis_id = vis_id.replace(", ", "_").replace(" ", "_")
    return URIRef(f"{diva_d}vis_{vis_id}_{uri_suffix}")

def get_dataset_uri(dataset_name, dataset_partition):
    """Generate a stable URI for a dataset based on its name and partition."""
    # Use a hash to ensure the URI is stable and unique
    return URIRef(f"{diva_d}dataset_{dataset_name}_{dataset_partition}")

def get_active_dataset():
    """Get the last active dataset URI where the active key is True."""
    for dataset_uri, metadata in reversed(list(datasets.items())):
        if metadata.get('active', False):
            return dataset_uri
    return None

def save_vis(view_uri, vis_uri):
    """Save the visualization URI in the global views dictionary."""
    dataset_uri = get_active_dataset()
    if dataset_uri is not None:
        datasets[dataset_uri]['views'][view_uri] = vis_uri

def get_active_vis(view_uri):
    """Get the active visualization URI from the global views dictionary."""
    dataset_uri = get_active_dataset()
    if dataset_uri is not None and view_uri in datasets[dataset_uri]['views']:
        return datasets[dataset_uri]['views'][view_uri]
       
    return None
        
def clear_vis(view_uri):
    """Clear the visualization URI from the global views dictionary."""
    dataset_uri = get_active_dataset()
    if dataset_uri is not None and view_uri in datasets[dataset_uri]['views']:
        del datasets[dataset_uri]['views'][view_uri] 
            
def disable_dataset(dataset_uri):
    """Toggle the active status of a dataset."""
    if dataset_uri in datasets:
        datasets[dataset_uri]['active'] = False
    else:
        print(f"Dataset {dataset_uri} does not exist in the global dataset dictionary.")

def enable_dataset(dataset_uri):
    """Toggle the active status of a dataset."""
    if dataset_uri in datasets:
        datasets[dataset_uri]['active'] = True
    else:
        print(f"Dataset {dataset_uri} does not exist in the global dataset dictionary.")

def add_field(field):
    field_uri = get_field_uri(field['name'], field['value'])
    g.add((field_uri, RDF.type, diva.Field))
    g.add((field_uri, RDFS.label, Literal(field['name'])))
    g.add((field_uri, diva.hasFieldType, field['type'])) # the type will depend on the field value (for now, we assume categorical)
    g.add((field_uri, RDF.value, Literal(field['value'])))

    g.add((field_uri, DCTERMS.title, Literal(f"Field {field['name']} = {field['value']}")))
    g.add((field_uri, DCTERMS.description, Literal(f"Field {field['name']} with value {field['value']}")))

    return field_uri

def add_view_manipulation(metadata, uri_suffix):
    # Creates the view manipulation associated to the action
    manipulation_uri = URIRef(f"{diva_d}view_manipulation_{uri_suffix}")
    g.add((manipulation_uri, RDF.type, diva.ViewManipulation))
    g.add((manipulation_uri, diva.hasViewManipulationType, metadata['manipulation_type']))

    if metadata['ui_element'] is not None:
        g.add((manipulation_uri, diva.hasUIElement, metadata['ui_element']))
    
    return manipulation_uri

def add_action(metadata, event_time, uri_suffix):

    action_uri = URIRef(f"{diva_d}action_{uri_suffix}")
    g.add((action_uri, RDF.type, diva.Action))
    g.add((action_uri, diva.hasActionType, metadata['action_type']))
    g.add((action_uri, PROV.wasAssociatedWith, user_uri))
    g.add((action_uri, PROV.startedAtTime, event_time))
    g.add((action_uri, DCTERMS.description, Literal(metadata['description'])))
    g.add((action_uri, RDFS.label, Literal(metadata['title'])))

    return action_uri

def add_event(metadata, uri_suffix):
    # Creates the event associated to the view manipulation
    event_uri = URIRef(f"{diva_d}event_{uri_suffix}")
    g.add((event_uri, RDF.type, diva.Event))
    g.add((event_uri, diva.hasEventType, metadata['event_type']))

    return event_uri

def add_unknown_vis(uri_suffix):
    unknown_vis_uri = URIRef(f"{diva_d}unknown_vis_{uri_suffix}")
    g.add((unknown_vis_uri, RDF.type, diva.Visualization))
    g.add((unknown_vis_uri, DCTERMS.title, Literal("Unknown Visualization")))
    return unknown_vis_uri

def handle_remove(metadata, view_uri, event_time, uri_suffix):

    action_uri = add_action(metadata, event_time, uri_suffix)

    # Assign the entity (visualization) used in the action
    vis_uri = get_active_vis(view_uri)  # Get the active visualization in the view

    if vis_uri is None:
        if metadata['visualization']['class'] is not None:
            vis_uri = create_vis(metadata['visualization'], uri_suffix)        
        else:
            vis_uri = add_unknown_vis(uri_suffix)

    g.add((action_uri, PROV.used, vis_uri))

    manipulation_uri = add_view_manipulation(metadata, uri_suffix)

    event_uri = add_event(metadata, uri_suffix)
    g.add((manipulation_uri, diva.hasEvent, event_uri))

    g.add((action_uri, PROV.used, manipulation_uri))

    clear_vis(view_uri)  # Clear the visualization from the view

    return action_uri

def handle_create(metadata, view_uri, event_time, uri_suffix):

    # Creates the action of creating a visualization
    # It does not have a prov:used, as it is not associated with a specific visualization yet
    action_uri = add_action(metadata, event_time, uri_suffix)
    manipulation_uri = add_view_manipulation(metadata, uri_suffix)

    event_uri = add_event(metadata, uri_suffix)
    g.add((manipulation_uri, diva.hasEvent, event_uri))

    g.add((action_uri, PROV.used, manipulation_uri))
    
    vis_uri = create_vis(metadata['visualization'], uri_suffix)

    g.add((vis_uri, PROV.wasGeneratedBy, action_uri)) # The visualization is generated by the action

    if 'view_ui_elements' in metadata:
        for ui_element in metadata['view_ui_elements']:
            g.add((view_uri, diva.hasUIElement, ui_element))

    g.add((view_uri, diva.hasVisualization, vis_uri))

    save_vis(view_uri, vis_uri)  # Save the visualization in the view

    return action_uri

def handle_modify(metadata, view_uri, event_time, uri_suffix):
   
    action_uri = add_action(metadata, event_time, uri_suffix)
    manipulation_uri = add_view_manipulation(metadata, uri_suffix)
    event_uri = add_event(metadata, uri_suffix)

    g.add((manipulation_uri, diva.hasEvent, event_uri))

    g.add((action_uri, PROV.used, manipulation_uri))

    vis_uri = None
    if 'visualization' in metadata:
        vis_uri = create_vis(metadata['visualization'], uri_suffix)

    if 'view_ui_elements' in metadata:
        for ui_element in metadata['view_ui_elements']:
            g.add((view_uri, diva.hasUIElement, ui_element))
    
    last_vis_state = get_active_vis(view_uri)  # Get the last active visualization in the view
    if last_vis_state is not None:
        g.add((action_uri, PROV.used, last_vis_state))
        if vis_uri is not None :
            g.add((vis_uri, PROV.wasDerivedFrom, last_vis_state))  # The new visualization is derived from the last state

    if vis_uri is not None:
        save_vis(view_uri, vis_uri)  # Save the visualization in the view

    return action_uri

def handle_switch(metadata, view_uri, event_time, uri_suffix):

    action_uri = add_action(metadata, event_time, uri_suffix)
    manipulation_uri = add_view_manipulation(metadata, uri_suffix)
    event_uri = add_event(metadata, uri_suffix)

    g.add((manipulation_uri, diva.hasEvent, event_uri))
  
    g.add((action_uri, PROV.used, manipulation_uri))

    vis_uri = get_active_vis(view_uri)  # Get the active visualization in the view

    if vis_uri is None:
        vis_uri = add_unknown_vis(uri_suffix)

    g.add((action_uri, PROV.used, vis_uri))  # The action uses the visualization

    new_vis_uri = create_vis(metadata['visualization'], uri_suffix)

    g.add((new_vis_uri, PROV.wasGeneratedBy, action_uri))  # The new visualization is generated by the action
    g.add((view_uri, diva.hasVisualization, new_vis_uri))  # The view has the new visualization
    g.add((action_uri, PROV.used, new_vis_uri))  # The action uses the new visualization

    if 'view_ui_elements' in metadata:
        for ui_element in metadata['view_ui_elements']:
            g.add((view_uri, diva.hasUIElement, ui_element))

    # Store the visualization in the view
    save_vis(view_uri, new_vis_uri)  
    

    return action_uri

def handle_global(metadata, event_time, uri_suffix):

    action_uri = add_action(metadata, event_time, uri_suffix)
    manipulation_uri = add_view_manipulation(metadata, uri_suffix)
    event_uri = add_event(metadata, uri_suffix)

    g.add((manipulation_uri, diva.hasEvent, event_uri))

    g.add((action_uri, PROV.used, manipulation_uri))

    
    current_dataset = get_active_dataset()
    g.add((action_uri, PROV.used, current_dataset))  # The action uses the current active dataset
    disable_dataset(current_dataset) # disable the current active dataset
    
    new_dataset_uri = get_dataset_uri(metadata['dataset']['location'], metadata['dataset']['spatialResolution'])
    if new_dataset_uri not in datasets: # Normal case: the dataset is already created
        new_dataset_uri = create_dataset(metadata['dataset'])
        g.add((new_dataset_uri, PROV.wasGeneratedBy, action_uri))  # The new dataset is generated by the action

    g.add((action_uri, PROV.used, new_dataset_uri))  # The action uses the new dataset
    enable_dataset(new_dataset_uri)

    return action_uri

def create_view(metadata, uri_suffix):    
    
    view_uri = URIRef(f"{diva_d}view_{metadata['view_title']}_{uri_suffix}")

    # Only create a new view in the graph if it doesn't exist
    view_data = datasets[get_active_dataset()]['views'].get(view_uri, None)
    if view_data is None:
        g.add((view_uri, RDF.type, metadata['view_type']))
        g.add((view_uri, DCTERMS.description, Literal(metadata['view_description'])))
        g.add((view_uri, DCTERMS.title, Literal(metadata['view_title'])))

    return view_uri

def create_vis(metadata, uri_suffix):
    
    vis_uri = get_vis_uri(metadata['id'], uri_suffix)
     
    g.add((vis_uri, RDF.type, metadata['class']))
    g.add((vis_uri, diva.hasDataSource, get_active_dataset()))  
    g.add((vis_uri, PROV.wasAttributedTo, user_uri))  # Associate the visualization with the user
    g.add((vis_uri, DCTERMS.title, Literal(metadata['title'])))
    g.add((vis_uri, DCTERMS.description, Literal(metadata['description'])))

    encodings = metadata.get('encodings', None)
    if encodings:
        for encoding in encodings:
            field = encoding.get('field')
            channel = encoding.get('channel')
            
            encoding_uri = get_encoding_uri(field['name'], field.get('value', None), channel.get('name', None))    
            
            g.add((encoding_uri, RDF.type, diva.Encoding))
            
            channelConcept = channel.get('concept', None)
            if channelConcept is not None:
                g.add((encoding_uri, diva.hasEncodingChannel, channelConcept))

            g.add((encoding_uri, diva.hasEncodingField, add_field(field)))

            g.add((encoding_uri, DCTERMS.description, Literal(f"Encoding for field {field['name']}")))

            g.add((vis_uri, diva.hasEncoding, encoding_uri))

            hasLegend = encoding.get('legend', None)
            if hasLegend is not None:
                g.add((encoding_uri, diva.hasLegend, diva.Legend))  # Associate the encoding with the legend            

    # Add the interactive signals of the visualization
    signals = metadata.get('signals', [])
    for signal in signals:
        signal_uri = get_signal_uri(signal['id'], signal['value'])
        g.add((signal_uri, RDF.type, diva.Signal))
        g.add((signal_uri, diva.hasSignalType, signal['type']))
        g.add((signal_uri, RDF.value, Literal(signal['value']))) 
        g.add((signal_uri, DCTERMS.title, Literal(f"Signal {signal['id']} = {signal['value']}")))
        g.add((signal_uri, DCTERMS.description, Literal(f"Signal {signal['id']} with value {signal['value']}")))

        g.add((vis_uri, diva.hasSignal, signal_uri))
     
    return vis_uri

def create_dataset(metadata):

    dataset_uri = get_dataset_uri(metadata['location'], metadata['spatialResolution'])

    if dataset_uri in datasets:
        return dataset_uri
    
    datasets[dataset_uri] = { 'views': {}, 'active': True }

    g.add((dataset_uri, RDF.type, diva.DataSource))
    g.add((dataset_uri, DCTERMS.title, Literal(metadata['title'])))
    g.add((dataset_uri, DCTERMS.issued, Literal(metadata['issued'], datatype=XSD.gYear)))

    agent_uri = URIRef(f"{diva_d}agent_{metadata['creator']}")
    g.add((agent_uri, RDF.type, FOAF.Agent))
    g.add((agent_uri, FOAF.name, Literal(metadata['creator'])))
    g.add((dataset_uri, DCTERMS.creator, agent_uri))

    publisher_uri = URIRef(f"{diva_d}publisher_{metadata['publisher']}")
    g.add((publisher_uri, RDF.type, FOAF.Agent))
    g.add((publisher_uri, FOAF.name, Literal(metadata['publisher'])))
    g.add((dataset_uri, DCTERMS.publisher, publisher_uri))

    return dataset_uri

def create_user(user_name):
    global user_uri
  
    user_uri = URIRef(f"{diva_d}{user_name}")

    g.add((user_uri, RDF.type, PROV.Agent))
    g.add((user_uri, FOAF.name, Literal(user_name)))

def create_exploration_path(user_name):

    exploration_path_uri = URIRef(f"{diva_d}explorationPath_{user_name}")

    if exploration_path_uri in exploration_paths:
        return exploration_path_uri
    
    exploration_paths[exploration_path_uri] = []
    g.add((exploration_path_uri, RDF.type, diva.ExplorationPath))
    g.add((exploration_path_uri, DCTERMS.title, Literal(f"Exploration Path for {user_name}")))

    return exploration_path_uri
    
def generate_username():
    return f"user_{len(users) + 1}"

def create_rdf_from_json(json_data):
    
    parser = LogParser(json_data)
    
    # Exploration path setup
    # user_name = parser.get_user()
    user_name = generate_username()
    users.append(user_name)
    create_user(user_name)  
    exploration_path_uri = create_exploration_path(user_name)

    for index, event in enumerate(json_data):

        event_id = len(exploration_paths[exploration_path_uri]) + 1  # Unique event ID based on the current length of the exploration path
        exploration_paths[exploration_path_uri].append(index)  # Store the index of the event in the exploration path
        
        event_time = Literal(parser.get_action_time(index), datatype=XSD.dateTime)

        # Create the dataset if it doesn't exist
        dataset_metadata = parser.get_dataset_metadata(index)
        create_dataset(dataset_metadata)

        view_metadata = parser.get_view_metadata(index)
        view_uri = None
        if view_metadata is not None:
            view_uri = create_view(view_metadata, get_entity_suffix(user_name))

        action_type = parser.get_action_type(index)
        if action_type == 'remove':
            remove_metadata = parser.get_remove_metadata(index)
            action_uri = handle_remove(remove_metadata, view_uri, event_time, get_event_suffix(user_name, 'remove', event_id))

        elif action_type == 'add':
            add_metadata = parser.get_add_vis_metadata(index)
            action_uri = handle_create(add_metadata, view_uri, event_time, get_event_suffix(user_name, 'create', event_id))

        elif action_type == 'switch':
            switch_metadata = parser.get_switch_metadata(index)
            action_uri = handle_switch(switch_metadata, view_uri, event_time, get_event_suffix(user_name, 'switch', event_id))

        elif action_type == 'global':
            global_metadata = parser.get_global_metadata(index)
            action_uri = handle_global(global_metadata, event_time, get_event_suffix(user_name, 'global', event_id))

        elif action_type == 'modify':
            modify_metadata = parser.get_modify_metadata(index)
            if modify_metadata is None:
                print(f"Warning: No modify metadata found for event ID {event_id}. Skipping.")
                continue
            action_uri = handle_modify(modify_metadata, view_uri, event_time, get_event_suffix(user_name, 'modify', event_id))

        if action_uri:
            rdf_seq_property = URIRef(f"{rdf_ns}_{event_id}")
            g.add((exploration_path_uri, rdf_seq_property, action_uri))  
        else:
            print(f"Warning: No action URI created for event ID {event_id}. Skipping.")

def init_globals():
    global g, datasets

    g = Graph()
    g.bind("diva", diva)
    g.bind("", diva_d)
    g.bind("diva_th", diva_th)

    g.bind("prov", PROV)
    g.bind("dcterms", DCTERMS)
    g.bind("foaf", FOAF)
    g.bind("dcat", DCAT)

    # Initialize other globals
    datasets = {} 

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python lifting-estime-to-diva.py <input_dir> <output_dir>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    
    global exploration_paths, users
    exploration_paths = {}
    users = []

    for filename in sorted(os.listdir(input_dir)):
        if not filename.endswith('.json'):
            continue

        input_file = os.path.join(input_dir, filename)
        output_file = os.path.join(output_dir, os.path.splitext(filename)[0] + '.ttl')

        # Re-initialize all globals before processing each file
        init_globals()

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        except FileNotFoundError:
            print(f"Error: File '{input_file}' not found")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in file '{input_file}'")
            sys.exit(1)

        try:
            create_rdf_from_json(json_data)  # modifies global g and others
        except Exception as e:
            print(f"Error processing JSON in file '{input_file}': {e}")
            traceback.print_exc(); 
            sys.exit(1)

        try:
            g.serialize(destination=output_file, format='turtle')
            print(f"✅ Successfully converted {input_file} → {output_file}")
        except Exception as e:
            print(f"Error writing output file '{output_file}': {e}")