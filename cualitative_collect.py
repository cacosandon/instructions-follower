IALAB_USER = 'jiossandon'

import os.path as osp
import json
import sys
import base64

matterport_build_path = f'/home/{IALAB_USER}/datasets/Matterport3DSimulator/build'
metadata_script_path = f'/home/{IALAB_USER}/repos/360-visualization/metadata_parser'
results_path = f'/home/{IALAB_USER}/storage/speaker_follower_with_objects/tasks/R2R/speaker/results/'

if matterport_build_path not in sys.path:
  sys.path.append(matterport_build_path)

if metadata_script_path not in sys.path:
  sys.path.append(metadata_script_path)

if results_path not in sys.path:
  sys.path.append(results_path)


import matplotlib

matplotlib.use('WebAgg')

import matplotlib.pyplot as plt

import MatterSim
import numpy as np
import networkx as nx
from parse_house_segmentations import HouseSegmentationFile
from collections import defaultdict
import random
import io

# load navigation graph to calculate the relative heading of the next location
def load_nav_graph(graph_path):
  with open(graph_path) as f:
    G = nx.Graph()
    positions = {}
    data = json.load(f)
    for i,item in enumerate(data):
      if item['included']:
        for j,conn in enumerate(item['unobstructed']):
          if conn and data[j]['included']:
            positions[item['image_id']] = np.array([item['pose'][3], item['pose'][7], item['pose'][11]])
            assert data[j]['unobstructed'][i], 'Graph should be undirected'
            G.add_edge(item['image_id'],data[j]['image_id'])
    nx.set_node_attributes(G, values=positions, name='position')
  return G

def compute_rel_heading(graph, current_viewpoint, current_heading, next_viewpoint):
  if current_viewpoint == next_viewpoint:
    return 0.
  target_rel = graph.nodes[next_viewpoint]['position'] - graph.nodes[current_viewpoint]['position']
  target_heading = np.pi/2.0 - np.arctan2(target_rel[1], target_rel[0]) # convert to rel to y axis

  rel_heading = target_heading - current_heading

  # normalize angle into turn into [-pi, pi]
  rel_heading = rel_heading - (2*np.pi) * np.floor((rel_heading + np.pi) / (2*np.pi))
  return rel_heading


def visualize_panorama_img(scan, viewpoint, heading, elevation):
  WIDTH = 80
  HEIGHT = 480
  pano_img = np.zeros((HEIGHT, WIDTH*36, 3), np.uint8)
  VFOV = np.radians(55)
  sim = MatterSim.Simulator()
  sim.setCameraResolution(WIDTH, HEIGHT)
  sim.setCameraVFOV(VFOV)
  sim.initialize()
  for n_angle, angle in enumerate(range(-175, 180, 10)):
    sim.newEpisode([scan], [viewpoint], [heading + np.radians(angle)], [elevation])
    state = sim.getState()
    im = state[0].rgb
    im = np.array(im)
    pano_img[:, WIDTH*n_angle:WIDTH*(n_angle+1), :] = im[..., ::-1]
  return pano_img

def visualize_tunnel_img(scan, viewpoint, heading, elevation):
  WIDTH = 640
  HEIGHT = 480
  VFOV = np.radians(60)
  sim = MatterSim.Simulator()
  sim.setCameraResolution(WIDTH, HEIGHT)
  sim.setCameraVFOV(VFOV)
  sim.init()
  sim.newEpisode(scan, viewpoint, heading, elevation)
  state = sim.getState()
  im = state.rgb
  return im[..., ::-1].copy()

# # Visualization


LABEL_MAPPING = {
  'a': 'bathroom',
  'b': 'bedroom',
  'c': 'closet',
  'd': 'dining room',
  'e': 'entryway/foyer/lobby',
  'f': 'familyroom',
  'g': 'garage',
  'h': 'hallway',
  'i': 'library',
  'j': 'laundryroom/mudroom',
  'k': 'kitchen',
  'l': 'living room',
  'm': 'meetingroom/conferenceroom',
  'n': 'lounge',
  'o': 'office',
  'p': 'porch/terrace/deck/driveway',
  'r': 'rec/game',
  's': 'stairs',
  't': 'toilet',
  'u': 'utilityroom/toolroom',
  'v': 'tv',
  'w': 'workout/gym/exercise',
  'x': 'outdoor areas containing grass, plants, bushes, trees, etc.',
  'y': 'balcony',
  'z': 'other room',
  'B': 'bar',
  'C': 'classroom',
  'D': 'dining booth',
  'S': 'spa/sauna',
  'Z': 'junk',
  '-': 'no label'
}

IMG_HEIGHT = 1440
IMG_WIDTH = 2880

def get_viewpoint_region_name(metadata, viewpoint):
  values = metadata.get_region(viewpoint).label.values
  if not values.size > 0:
      return 'no label'
  label_keyword = values[0]
  return LABEL_MAPPING[label_keyword]

def get_info(scan, viewpoint, viewpoint_heading, metadata, viewpoints_information):
  connectivity_path = f'/home/{IALAB_USER}/repos/360-visualization/connectivity/{scan}_connectivity.json'
  reachable_viewpoints = metadata.angle_relative_reachable_viewpoints(viewpoint, connectivity_path)

  images = []
  for viewpoint_elevation in (np.pi / 2 * x for x in range(-1, 2)):
    im = visualize_panorama_img(scan, viewpoint, viewpoint_heading, viewpoint_elevation)
    images.append(im)

  fig, ax = plt.subplots(1,1, figsize=(18,9))

  img = np.concatenate(images[::-1], axis=0)

  ax.imshow(img)
  plt.xticks(np.linspace(0, IMG_WIDTH - 1, 5), [-180, -90, 0, 90, 180])
  plt.xlabel(f'relative heading from the agent. -90° is left, 90° is right, and (-)180° is behind')
  plt.yticks(np.linspace(0, IMG_HEIGHT - 1, 5), [-180, -90, 0, 90, 180])

  x0, y0 = viewpoint_heading, 0

  reachable_viewpoints_array = reachable_viewpoints.itertuples()
  reachable_viewpoints_options = []
  for viewpoint_idx, reachable_viewpoint in enumerate(reachable_viewpoints_array):
    reachable_viewpoints_options.append(reachable_viewpoint)
    heading, elevation = float(reachable_viewpoint.heading), float(reachable_viewpoint.elevation)

    heading -= x0
    while heading > np.pi:
        heading -= 2 * np.pi
    while heading < -np.pi:
        heading += 2 * np.pi

    elevation += y0
    while elevation > np.pi:
        heading -= 2 * np.pi
    while elevation < -np.pi:
        elevation += 2 * np.pi

    first_coord = (heading / (2 * np.pi) + 0.5) * IMG_WIDTH
    second_coord = (0.5 - elevation / (np.pi / 1.1)) * IMG_HEIGHT

    ax.text(first_coord - 20, second_coord - 10, str(viewpoint_idx + 1), color='white', fontsize="x-large")
    ax.plot(first_coord, second_coord, color='blue', marker='o',
              markersize= 15 / reachable_viewpoint.distance, linewidth=1)

  f = io.BytesIO()
  plt.savefig(f, format="png", facecolor=(0.95, 0.95, 0.95))
  encoded_img = base64.b64encode(f.getvalue()).decode('utf-8').replace('\n', '')
  f.close()

  return reachable_viewpoints_options, encoded_img

def run_human_follower():
  viewpoints_information = defaultdict(dict)

  instructions_path = f'/home/{IALAB_USER}/storage/objects-auxiliary/paths/R2R_val_unseen.json'


  with open(instructions_path, 'r') as f:
    data = json.load(f)
    print(f"The file contain {len(data)} paths. The index must be between 0 and {len(data) - 1}.")
    instruction_data = random.choice(data)

  scan = instruction_data['scan']
  viewpoints_sequence = instruction_data['path']
  initial_heading = instruction_data['heading']
  path_id = instruction_data['path_id']

  base_models = [
    'speaker_base_',
    'new-craft-stairs-0_5_'
  ]

  models_names = [
    'SpeakerBase',
    'CraftLossStairs_0_5'
  ]

  speaker_model = 'speaker_teacher_imagenet_mean_pooled'
  dataset = 'val_unseen'
  iteration = 20000

  results_path = f'/home/{IALAB_USER}/storage/speaker_follower_with_objects/tasks/R2R/speaker/results/'

  paths = list(map(lambda base_path: results_path + f'{base_path}{speaker_model}_{dataset}_iter_{iteration}.json', base_models))

  datas = []
  for path in paths:
    with open(path, 'r') as file:
      datas.append(json.load(file))

  new_instructions_by_speaker = list(map(lambda data: ' '.join(data[f'{path_id}_0']['words']), datas))

  new_instructions_by_speaker_data = []
  for idx, instruction in enumerate(new_instructions_by_speaker):
    new_instructions_by_speaker_data.append({
      'model': models_names[idx],
      'instruction': instruction
    })


  # Craft instructions
  craft_instructions_path = f'/home/{IALAB_USER}/datasets/Matterport3DSimulator/tasks/R2R/data/craft_instructions_by_path_unseen.json'
  with open(craft_instructions_path, 'r') as file:
    crafts = json.load(file)
    craft_instruction_data = {
      'model': 'Craft',
      'instruction': crafts[f"{path_id}"]
    }

  # Humans instructions

  humans_instructions = instruction_data['instructions']
  human_instruction_data = {
    'model': 'Human',
    'instruction': random.choice(humans_instructions),
  }

  instruction_to_eval = random.choice(new_instructions_by_speaker_data + [human_instruction_data, craft_instruction_data])


  EXPERIMENT_NAME = 'prod'
  if EXPERIMENT_NAME == 'testing':
    instruction_to_eval = craft_instruction_data

  return scan, path_id, viewpoints_sequence, viewpoints_information, initial_heading, instruction_to_eval



