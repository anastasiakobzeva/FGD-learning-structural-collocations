import re
import xml.etree.ElementTree as ET
import xml
import string
import os
import nltk


 # Set this variable to True to print info messages
verbose_default = False


failing_labels = []
worked_ids = []


def write_file(filename:str, lines:str) -> None:
    """ Writing out a file based on array of strings (lines) """
    with open(filename, 'w', encoding="utf-8") as file:
        for line in lines:
            file.write(line)


def split_sentences(xml_file: xml.etree.ElementTree.Element) -> list:
    """
    Split the xml into smaller xml pieces corresponding to sentences (<s> ... </s>)
    :param xml: tiger xml-file with parsed sentences
    :return: list with sentence parses in xml
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    sentences = [sent for sent in root.iter('s')]
    return sentences


def get_IDs(sentence: xml.etree.ElementTree.Element, 
            verbose: bool = verbose_default) -> tuple:
    """
    Extract IDs from sentence object
    :param sentence: tiger xml object with one parsed sentence
    :param verbose: boolean, True for info messages
    :return: list with ids as strings
    """
    # 
    sentence_id = sentence.attrib['id']
    graph_id = sentence[0].attrib['root']
    web_id = graph_id.split('_')[0][1:] # id as displayed on the website
    if verbose:
        print('INFO:', f'IDs: web_id:{web_id}, graph_id: {graph_id},',
              f'sentence_id: {sentence_id}')
    return web_id, graph_id, sentence_id


def create_graph(sentence: xml.etree.ElementTree.Element,
                 verbose:bool = verbose_default) -> dict:
    """
    Create a dictionary with c-structure graph elements 
    :param sentence: an xml object corresponding to a sentence (<s> ... </s>)
    :return: a graph dictionary for the c-structure, as well as dictionaries
                indexing node labels with ids and vice versa
    """
    graph = dict()
    for child in sentence[0][0]:  # terminals
        for i in child.attrib:
            if i == 'word':  # only terminals representing words are needed
                if child.attrib[i] != '--':
                    node = (child.attrib[i], child.attrib['id'])
                    graph[node] = ''
    for child in sentence[0][1]:  # non-terminals
        for l_child in child:  # nt egdes
            if 'f' not in l_child.attrib['idref']:  # excluding references to f structure
                node = (child.attrib['cat'], child.attrib['id'])
                if node not in graph:
                    graph[node] = [l_child.attrib['idref']]
                else:
                    graph[node].append(l_child.attrib['idref'])
    
    # convert to alternative dictionary structure
    # keys: node ids, values: dictionary 
    #                         key:        value:
    #                         name        node name as str
    #                         child_ids   list with node ids of children
    #                                     '' if no children
    alternative_graph = dict()
    for node in graph:
        alternative_graph[node[1]] = {'name': node[0], 
                                      'child_node_ids': graph[node],
                                      'parent_node_ids': set()}
    for node in alternative_graph:
        for child_node in alternative_graph[node]['child_node_ids']:
            if verbose:
                print(f"node: {node}, child_node: {child_node}")
            alternative_graph[child_node]['parent_node_ids'].add(node)
    
    # create dictionaries mapping node ids and names
    node_names = dict()
    node_ids = dict()
    for node in graph:
        node_names[node[1]] = node[0]
        node_ids[node[0]] = node[1]
        
    graph = alternative_graph
    
    return graph, node_ids, node_names


def recursive_lookup(graph:dict, curr_id:str) -> str:
    """
    Generates a nltk-compatible string representation of graph, starting from
    the node with id curr_id.
    :param graph: data structure as defined by create_graph
    :param curr_id: starting node
    :return: nltk-compatible string representation
    """
    if len(graph[curr_id]['child_node_ids']) == 0:
        return ' ' + graph[curr_id]['name']
    else:
        curr_str = ''
        for child in graph[curr_id]['child_node_ids']:
            if len(graph[child]['child_node_ids']) == 0:
                curr_str += recursive_lookup(graph, child)
            else:
                curr_str += recursive_lookup(graph, child) + ')'
        curr_str = '(' + graph[curr_id]['name'] + curr_str
        return curr_str


def convert_graph_to_nltk_tree(graph:dict, 
                               root_id:str,
                               verbose:bool = verbose_default) \
    -> nltk.tree.tree.Tree:
    """
    Generate nltk compatible string representation of entire sentence by
    starting at the root node.
    
    :param imported_dict: graph dictionary as defined by create_graph()
    :param root: id of the first node (xml root)
    :return: nltk Tree object
    """
    nltk_str = recursive_lookup(graph, root_id)
    if verbose:
        print(f"INFO: nltk_str={nltk_str}")
    tree = nltk.tree.tree.Tree.fromstring(nltk_str + ')')
    return tree


def extract_text(nltk_tree: nltk.tree.tree.Tree) -> str:
    """
    Extract sentence text (without commas so that it can be written into a csv)
    :param nltk_tree: nltk-tree object with C-structure
    :return: sentence string
    """
    leaves = nltk_tree.leaves()
    punctuation = set(string.punctuation)
    text = ''.join(w if set(w) <= punctuation else ' ' + w for w in leaves).lstrip()
    text = text.replace('« ', '«').replace(' »', '»')
    text = text.replace('–', '').replace(',', '').replace('—', '')
    words = text.strip().split()
    words[0] = words[0].title()  # to get words inside «» as upper case
    text = ' '.join(words)
    return text


def find_pred(sentence: xml.etree.ElementTree.Element,
              eligible_values:list = ['pro', 'hvor', 'hvorfor', 'hvordan',
                                      'når'],
              verbose: bool = verbose_default) -> tuple:
    """
    Find all PRED f-structure terminals that have a value from eligible_values.
    :param sentence: sentence tree in xml
    :param eligible_values: PRED values to be found
    :param verbose: information message output switch
    :return: list of f-levels (represented as number strings) that contain a
                 PRED terminal with a value from eligible_values
             and a list of the corresponding pred as str
    """
    pro_f_levels = list()
    pred_values = list()
    for t_node in sentence[0][0]:  # terminals
        if t_node.attrib['val'] in eligible_values:
            m = re.match(".*_(.+?)_PRED", t_node.attrib['id'])
            if m is not None:
                pred_values.append(t_node.attrib['val'])
                pro_f_levels.append(m.group(1))
    if verbose:
        print(f"INFO: pro_f_levels: {pro_f_levels}")
        print(f"INFO: corresponding pred_values: {pred_values}")
    return pro_f_levels, pred_values


def find_edges(sentence: xml.etree.ElementTree.Element,
               f_levels: list,
               pred_values: list, 
               dependency_type: str = "TOPIC-REL",
               verbose: bool = verbose_default) \
    -> tuple:
    """
    Find all edges on the f-structure levels defined in f_levels with an 
    embedding relation of type dependency_type.
    For the moment, dependency_type has been tested with
        - FOCUS-INT (-> wh dependency)
        - TOPIC-REL (-> relativization dependency)
    The edges of all non-terminal nodes are checked whether they indicate the 
    target dependency_type.
    The ones that do are then checked if they are on the target level.
    The ones that are are then added to the truncation point list. 
    (This list is used later to extract the path from filler to gap from the
     sentence.)
    
    :param sentence: sentence tree in xml
    :param f_levels: a list returned by find_pred 
                        (list of number strings)
    :param dependency_type: target dependency type
    :return: dict with edge ids as keys and corresponding pred labels as values 
                These edges indicate the target dependency type
             list of truncation points
    """
    edges = dict()
    truncation_points = list()
    for nt_node in sentence[0][1]:  # non-terminal nodes
        for nt_edge in nt_node:     # edges of non-terminal nodes
            if nt_edge.attrib['label'] == dependency_type: # dependency check
                for index, f in enumerate(f_levels):
                    if nt_edge.attrib['idref'].endswith(f):   # level check  
                        truncation_points.append(nt_node.attrib['id'])         # node is truncation point
                        edges[nt_edge.attrib['idref']] = pred_values[index]    # and has the right pred value ("pro")
    if verbose:
        print(f"INFO: pro under {dependency_type} and higher levels: {edges}")
        print(f"INFO: Truncation points: {truncation_points}")
    return edges, truncation_points


def find_syntactic_position(sentence: xml.etree.ElementTree.Element, 
                            f_level: str,
                            pred_value: str,
                            verbose:bool = verbose_default) -> str:
    """
    Find the syntactic position of PRED f-structure non-terminal on level 
    f_level with value pred_value.
    Check all non-terminals on level f_level if their label is one from 
    eligible_labels.
    
    :param sentence: sentence tree in xml
    :param f_level: f-level of pro under a dependency (str)
    :param pred_value: corresponding pred value (str)
    :return: syntactic position (str)
    """
    eligible_labels = ['SUBJ', 'OBJ', 'ADJUNCT', 'PREDLINK', 'OBL-TH']
    adjunct_pred_values = ['hvor', 'hvorfor', 'hvordan', 'når']
    position = ''
    
    for nt_node in sentence[0][1]:  # non-terminals
        for nt_edge in nt_node:     # nt edges
            if (nt_edge.attrib['idref'] == f_level and
                nt_edge.attrib['label'] in eligible_labels):
                position = nt_edge.attrib['label']
    if position == '':  # if position is not found or not in labels
        if verbose:
            print("WARNING [find_f_labels.find_syntactic_position]:"
                  "Syntactic position of 'pro' could not be found or the",
                  f"associated label is none of {eligible_labels}.",
                  f"f_level: {f_level}, pred_value: {pred_value},",
                  f"label of pro: {nt_edge.attrib['label']}.")
        failing_labels.append(nt_edge.attrib['label'])
        if pred_value in adjunct_pred_values:
            position = 'ADJUNCT'
            if verbose:
                print("INFO: Assigning ADJUNCT to position")
        else:
            print("ERROR [find_f_labels.find_syntactic_position]:"
                  'An unknown error occurred. Probably, the sentence is a',
                  'rhetorical question.')
    return position


def find_embedding_level_recursive(sentence: xml.etree.ElementTree.Element, 
                                   current_level: str, 
                                   initial_position = None,
                                   verbose: bool = verbose_default) -> str:
    """
    Identify path from current_level to its embedding level:
    For all f-structure non-terminals, identify edges on current level.
    If an edge is the initial position of the search, we have found its parent,
    the non-terminal whose edge we are looking at at the moment. Now, continue
    with the parent as the new current_level, until TOP is reached. 
    Not setting the initial_position variable again after entering the 
    recursion takes the first available edge.
    
    :param initial_position: nt edge label identifying search starting point
    :param sentence: sentence tree in xml
    :param cur_level: id of the current f-level (embedded; string)
    :return: path from the embedded level to the higher embedding level (f0; string)
    """
    if verbose:
        print("INFO: Find embedding level recursively")
        print(f"INFO: Current level: {current_level}")
    if current_level.endswith('f_0'):
        return 'TOP'
    else:
        parent_id = ''
        label = ''
        for nt_node in sentence[0][1]:  # non-terminals
            if 'f' in nt_node.attrib['id']:  # test if in f-structure
                for nt_edge in nt_node:
                    if nt_edge.attrib['idref'] == current_level:  # ignore adjunct cases
                        if initial_position is not None:
                            if nt_edge.attrib['label'] == initial_position:
                                label = nt_edge.attrib['label']
                                parent_id = nt_node.attrib['id']
                                if verbose:
                                    print("INFO: Found parent.",
                                          f"parent_id: {parent_id}")
                                break
                        else:
                            label = nt_edge.attrib['label']
                            parent_id = nt_node.attrib['id']
                            break
        return str(current_level + ', ' + label) + ' <- ' + \
            find_embedding_level_recursive(sentence=sentence, 
                                           current_level=parent_id)


def find_clause_type_modify_path(sentence: xml.etree.ElementTree.Element,
                                 path,
                                 verbose: bool = verbose_default) -> str:
    """
    Extract the clause type information from the previously extracted path from
    syntactical PRED position to TOP. Then, return the subpath from syntactical
    PRED position to the dependency filler.
    
    :param sentence: sentence tree in xml
    :param path: path as returned by recursive embedding level search
    :return: new path (list)
    """
    if verbose:
        print('INFO: path: ', path)
    new_path = {}
    path_elements = path[:-7].split(' <- ')  # list of strings of a format  's3392_0_f_7, SUBJ'; ' <- TOP' excluded
    if verbose:
        print('INFO: path elements: ', path_elements)
    clauses = {}  # label = f_level_tail, value = type of the clause/ statement
    for t_node in sentence[0][0]:  # terminals
        if t_node.attrib['id'].endswith('STMT-TYPE'):
            clauses[t_node.attrib['id'][:-10]] = t_node.attrib['val']  # not including '_STMT-TYPE' at the end
        elif t_node.attrib['id'].endswith('CLAUSE-TYPE'):
            clauses[t_node.attrib['id'][:-12]] = t_node.attrib['val']  # not including '_CLAUSE-TYPE' at the end
    if verbose:
        print('INFO: clause labels: ', clauses.keys())  # resulting format: s2977_7_f_0', 's2977_7_f_32' (like f-levels)
    for el in path_elements:  # strings of a format 's3392_0_f_7, SUBJ'
        id_node, label = el.split(', ')  # dividing string
        hit = [id_node == key for key in clauses.keys()]  # list of size n = len(clauses) with bool
        if any(hit):  # if bool == True (id in keys of clauses dict)
            hit_idx = hit.index(True)  # get the index of an element of clauses dict where it's the case
            new_label = label + '_' + list(clauses.items())[hit_idx][1]  # modify the label with clause info
        else:
            new_label = label
        new_path[new_label] = id_node
    if verbose:
        print('INFO: new path: ', new_path.items())
    return new_path


def truncate_path(truncation_point,
                  long_modified_path,
                  verbose:bool = verbose_default) -> str:
    """
    Shorten the path to the level embedding the dependency filler.
    
    :param long_modified_path:
    :param truncation_point: f-level that embeds dependency filler (end point
                                   for trucated path)
    :return: new truncated path (string)
    """
    if verbose:
        print("INFO: Truncating path.")
        print(f"INFO: truncation_point: {truncation_point}")
    new_path = ''
    hit = [truncation_point in value for value in long_modified_path.values()]
    if verbose:
        print(f'INFO: hit: {hit}')
    if any(hit):
        hit_idx = hit.index(True)  # returns the lowest index (first match)
        for i in range(hit_idx):
            label = list(long_modified_path.keys())[i]
            new_path += label
            new_path += ' '
    else:
        if truncation_point.endswith('0'):  # 0 f-lvl is not included into the long path, the old path should be correct
            new_path = ' '.join(list(long_modified_path.keys()))  # old path; joining the keys of that dict with a space
            if verbose:
                print(f"INFO: truncated path: {new_path}")
        else:
            if verbose:
                print('WARNING [find_f_labels.truncate_path]:',
                      'Truncation point is not in long path.',
                      "long path: ", long_modified_path,
                      f"truncation point: {truncation_point}")
    return new_path


def clean_path(truncated_path: str,
               verbose:bool = verbose_default) -> str:
    """
    Clean the path with labels by removing $-labels and modifying labels 
    with phrase structure information.
    :param truncated_path: path as returned by truncate_path
    :return: cleaned path (string)
    """
    if verbose:
        print('INFO: Cleaning path')
        print(f'INFO: Truncated path: {truncated_path}')
    if '$' in truncated_path:  # braces are in the f-structure and '$' is in path
        idx = [i.start() for i in list(re.finditer('\\$', truncated_path))]  # list of all indexes of '$'
        labels_with_ranges = {(el.start(), el.end()): truncated_path[el.start():el.end()]  # dict of path elements
                              for el in re.finditer(r'\S+', truncated_path)}              # with their positions as keys
        if verbose:
            print(f'INFO: labels_with_ranges: {labels_with_ranges}')
        new_dict = dict(labels_with_ranges)
        for rang, label in labels_with_ranges.items():
            if rang[0] in idx:
                if rang[0] + 1 != rang[1]:  # if it contains clause type info
                    tail = label[1:]
                    next_el_start = rang[1] + 1
                    next_tuple = [(k, v) for k, v in labels_with_ranges.items() if k[0] == next_el_start][0]
                    new_dict[next_tuple[0]] = next_tuple[1] + tail  # changing the new dictionary
                    new_dict.pop(rang)
                else:  # if it does not contain clause type info, we just remove it
                    new_dict.pop(rang)
        new_path = ' '.join(list(new_dict.values()))
    else:
        new_path = truncated_path
    if verbose:
        print(f'INFO: cleaned path: {new_path}')
    return new_path


def analyze_one_dependency(sentence: xml.etree.ElementTree.Element,
                           truncation_point,
                           f_level: str,
                           pred_value: str,
                           sentence_str: str,
                           verbose:bool = verbose_default) -> str:
    """
    Analyze one FG-dependency of a sentence, returning as formatted str.
    Analysis steps:
        1. Find syntactic position of the gap.
        2. Identify the path from that position to the top
        3. Truncate the path to the level embedding the filler.
        4. Clean up the path 
        5. Add path to the gap position for function output
    :param sentence: sentence tree in xml
    :param truncation_point: point where to truncate the long path (level of dependency)
    :param f_level: f-structure level of pred with value pred_value under target dependency
    :param pred_value: target value of pred f-structure non-terminal
    :param sentence_str: sentence text for easier lookup
    :param verbose: information message output switch
    :return: info as str
    """
    if verbose:
        print('INFO: Analyzing dependency.')
        
    _, _, sentence_id = get_IDs(sentence)
    cleaned_path = ''
    truncated_path = ''
    position = find_syntactic_position(sentence, f_level, pred_value)
    if position != '':
        try:
            path = find_embedding_level_recursive(sentence, f_level, position)
            modified_path = find_clause_type_modify_path(sentence, path)
            truncated_path = truncate_path(truncation_point, modified_path)
            try:
                cleaned_path = clean_path(truncated_path)
                worked_ids.append(sentence_id + '\n')
            except IndexError:
                print('ERROR [find_f_labels.analyze_one_dependency]:',
                      'Index error when cleaning the path')
        except RecursionError:
            print('ERROR [find_f_labels.analyze_one_dependency]:',
                  'Recursion error when finding the path.')
    else:
        if verbose:
            print('WARNING [find_f_labels.analyze_one_dependency]:',
                  'Pro position not found for:\n', sentence_str, '\n')
    cleaned_path = ' '.join(list(reversed(cleaned_path.split())))
    return position + ',' + cleaned_path + '\n'


def main():
    verbose = verbose_default
    
    xml_filename = 'rc_example.xml'
    folder = "examples"
    
    folder_path = os.path.abspath(folder)
    xml_filename = folder_path + os.path.sep + xml_filename
        
    # parse sentences
    with open(xml_filename, encoding='utf-8') as file:
        sentences = split_sentences(file)
    
    # initialize content to write to output file
    out = list()
    out.append('web_id,sent_id,graph_id,text,pro_position,cleaned_path\n')
    
    if verbose:
        print("INFO: Starting sentence analysis.")
    
    for sentence in sentences:   
        ### c-structure steps - easiest for sentence text extraction
        web_id, graph_id, sentence_id = get_IDs(sentence)
        graph, node_ids, node_names = create_graph(sentence)
        root_name = sentence[0][1][0].attrib['cat'] # root node label as string
        root_node_id = node_ids[root_name]
        nltk_tree = convert_graph_to_nltk_tree(graph, root_node_id)
        sentence_str = extract_text(nltk_tree)
        if verbose:
            print(f"INFO: Sentence text: {sentence_str}")

        ### f-structure steps
        
        # Find all PRED f-structure terminals that have one of the eligible values.
        pro_f_levels, pred_values = \
            find_pred(sentence, 
                      eligible_values = ['pro', 'hvor', 'hvorfor', 'hvordan', 
                                         'når'])
        # Find all f-structure edges on previously found levels with the 
        # specific dependency type under investigation.
        edges, truncation_points = \
            find_edges(sentence, pro_f_levels, pred_values, 
                       dependency_type = "TOPIC-REL")
        
        line = f"{web_id},{sentence_id},{graph_id},{sentence_str},"
        
        if len(edges) == 1: # analyzing only one dependency for now
            k = 0
        # for k, edge in enumerate(edges):
            result = analyze_one_dependency(sentence,
                                            truncation_point =
                                                truncation_points[k],
                                            f_level=list(edges.keys())[k],
                                            pred_value=pred_values[k],
                                            sentence_str=sentence_str)
            out.append(line + result)
            if verbose:
                print(f"INFO: Analysis result: {line}\n\n")
    filename = xml_filename.replace('xml', 'csv')
    write_file(filename, out)
    return out

if __name__ == '__main__':
    results = main()
    # pass
    