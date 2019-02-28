"""
[Universal Sentence Encoder](https://arxiv.org/abs/1803.11175) featurizer

From
https://scalableminds.com/blog/MachineLearning
/2018/08/rasa-universal-sentence-encoder/

Thanks Scalable Minds - we should probably tell them about this
https://scalableminds.com/#contact-us
"""

from rasa_nlu.featurizers import Featurizer

import os
import tensorflow_hub as hub
import tensorflow as tf


class UniversalSentenceEncoderFeaturizer(Featurizer):
    """Appends a universal sentence encoding to the message's text_features."""

    # URL of the TensorFlow Hub Module
    TFHUB_URL = "https://tfhub.dev/google/universal-sentence-encoder/2"

    name = "universal_sentence_encoder_featurizer"

    # We don't require any previous pipline step and return text_features
    requires = []
    provides = ["text_features"]

    def __init__(self, component_config):

        super(UniversalSentenceEncoderFeaturizer,
              self).__init__(component_config)

        # Set the tfhub cache directory in the case it changes
        os.environ["TFHUB_CACHE_DIR"] = '/tmp/tfhub'

        # Load the TensorFlow Hub Module with pre-trained weights
        sentence_encoder = hub.Module(self.TFHUB_URL)
        # Create a TensorFlow placeholder for the input string
        self.input_string = tf.placeholder(tf.string, shape=[None])
        # Invoke `sentence_encoder` in order to create the encoding tensor
        self.encoding = sentence_encoder(self.input_string)

        # Create a TensorFlow Session and run initializers
        self.session = tf.Session()
        self.session.run([tf.global_variables_initializer(),
                          tf.tables_initializer()])

    def train(self, training_data, config, **kwargs):

        # Nothing to train, just process all training examples so that the
        # feature is set for future pipeline steps
        for example in training_data.training_examples:
            self.process(example)

    def process(self, message, **kwargs):

        # Get the sentence encoding by feeding the message text and computing
        # the encoding tensor.
        feature_vector = self.session.run(self.encoding,
                                          {self.input_string:
                                           [message.text]})[0]
        # Concatenate the feature vector with any existing text features
        features = self._combine_with_existing_text_features(
            message, feature_vector)
        # Set the feature, overwriting any existing `text_features`
        message.set("text_features", features)

    @classmethod
    def load(cls, model_dir=None, model_metadata=None, cached_component=None,
             **kwargs):
        """Load this component from file."""

        if cached_component:
            return cached_component
        else:
            component_config = model_metadata.for_component(cls.name)
            return cls(component_config)
