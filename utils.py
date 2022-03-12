import networkx as nx
import json
import numpy as np

def select_options(viewpoints_length):
  move_to_node_options = [
    {
      "label": f"Move to node {i}",
      "value": f"node-{i}"
    } for i in range(1, viewpoints_length + 1)
  ]

  turn_options = [
    { "label": "Turn left ⬅️", "value": "turn-left" },
    { "label": "Turn right ➡️", "value": "turn-right" },
    { "label": "Turn around ⬇️", "value": "turn-around" },
  ]

  stop_option = [ { "label": "Stop here. I think this is the goal.", "value": "stop" } ]

  return [move_to_node_options] + [turn_options] + [stop_option]

def load_nav_graph(scan):
    """ Load connectivity graph for each scan """

    def distance(pose1, pose2):
        """ Euclidean distance between two graph poses """
        return ((pose1['pose'][3] - pose2['pose'][3]) ** 2
                + (pose1['pose'][7] - pose2['pose'][7]) ** 2
                + (pose1['pose'][11] - pose2['pose'][11]) ** 2) ** 0.5

    with open('connectivity/%s_connectivity.json' % scan) as f:
        G = nx.Graph()
        positions = {}
        data = json.load(f)
        for i, item in enumerate(data):
            if item['included']:
                for j, conn in enumerate(item['unobstructed']):
                    if conn and data[j]['included']:
                        positions[item['image_id']] = np.array([item['pose'][3],
                                                                item['pose'][7], item['pose'][11]])
                        assert data[j]['unobstructed'][i], 'Graph should be undirected'
                        G.add_edge(item['image_id'], data[j]['image_id'], weight=distance(item, data[j]))
        nx.set_node_attributes(G, values=positions, name='position')

    return G