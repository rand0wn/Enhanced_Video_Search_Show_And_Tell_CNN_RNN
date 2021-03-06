# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
r"""Generate captions for images using default beam search parameters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math
import os

import tensorflow as tf
import inference_wrapper

# Folder Lib Import
import sys
sys.path.insert(0, os.getcwd() + '/inference_utils')
# Folder Lib Import
import configuration
import caption_generator
import vocabulary


tf.logging.set_verbosity(tf.logging.INFO)

# Function to generate captions
def img_captions(file_inputs):
  # Build the inference graph.
  g = tf.Graph()
  with g.as_default():
    model = inference_wrapper.InferenceWrapper()
    restore_fn = model.build_graph_from_config(configuration.ModelConfig(),
                                               file_inputs[0])
  g.finalize()

  # Create the vocabulary.
  vocab = vocabulary.Vocabulary(file_inputs[1])

  filenames = []
  for file_pattern in file_inputs[2].split(","):
    filenames.extend(tf.gfile.Glob(file_pattern))
  tf.logging.info("Running caption generation on %d files matching %s",
                  len(filenames), file_inputs[2])

  with tf.Session(graph=g) as sess:
    # Load the model from checkpoint.
    restore_fn(sess)

    # Prepare the caption generator. Here we are implicitly using the default
    # beam search parameters. See caption_generator.py for a description of the
    # available beam search parameters.
    generator = caption_generator.CaptionGenerator(model, vocab)

    caption_list = list()
    prob_list = list()
    for filename in filenames:
      with tf.gfile.GFile(filename, "rb") as f:
        image = f.read()
      captions, probs = generator.beam_search(sess, image)
      prob_list.append('['+", ".join(map(str, probs))+']')

      loc_cap_list = list()
      for i, caption in enumerate(captions):
        # Ignore begin and end words.
        sentence = [vocab.id_to_word(w) for w in caption.sentence[1:-1]]
        sentence = " ".join(sentence).split('<S>')[0]
        loc_cap_list.append([sentence, math.exp(caption.logprob)])
      caption_list.append(loc_cap_list)
  return prob_list, caption_list