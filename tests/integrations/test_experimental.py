import pytest

from tests.integrations import cluster_utils as cluster_utils
from tests.integrations import config as conf
from tests.integrations import experiment as exp


@pytest.mark.nightly  # type: ignore
def test_nas_search() -> None:
    config = conf.load_config(conf.experimental_path("nas_search/train_one_arch.yaml"))
    config = conf.set_max_steps(config, 2)

    exp.run_basic_test_with_temp_config(config, conf.experimental_path("nas_search"), 1)


@pytest.mark.nightly  # type: ignore
def test_bert_glue() -> None:
    config = conf.load_config(conf.experimental_path("bert_glue_pytorch/const.yaml"))
    config = conf.set_max_steps(config, 2)

    exp.run_basic_test_with_temp_config(config, conf.experimental_path("bert_glue_pytorch/"), 1)


@pytest.mark.nightly  # type: ignore
@cluster_utils.skip_test_if_not_enough_gpus(1)
def test_faster_rcnn() -> None:
    config = conf.load_config(conf.experimental_path("FasterRCNN_tp/16-gpus.yaml"))
    config = conf.set_max_steps(config, 2)
    config = conf.set_slots_per_trial(config, 1)

    exp.run_basic_test_with_temp_config(
        config, conf.experimental_path("FasterRCNN_tp"), 1, max_wait_secs=4800
    )


@pytest.mark.nightly  # type: ignore
def test_mnist_tp_to_estimator() -> None:
    config = conf.load_config(conf.experimental_path("mnist_tp_to_estimator/const.yaml"))
    config = conf.set_max_steps(config, 2)

    exp.run_basic_test_with_temp_config(config, conf.experimental_path("mnist_tp_to_estimator"), 1)


@pytest.mark.nightly  # type: ignore
def test_resnet50() -> None:
    config = conf.load_config(conf.experimental_path("resnet50_tf_keras/const.yaml"))
    config = conf.set_max_steps(config, 2)

    exp.run_basic_test_with_temp_config(config, conf.experimental_path("resnet50_tf_keras"), 1)
