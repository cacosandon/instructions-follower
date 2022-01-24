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
