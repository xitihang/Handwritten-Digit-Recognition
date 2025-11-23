from core.trainer import Trainer
from config.config_manager import ConfigManager
from core.model_factory import ModelFactory


def handle_train_request():
    config_manager = ConfigManager()
    model_factory = ModelFactory(config_manager)

    def progress_update(log):
        # 这里可以通过WebSocket或HTTP流式返回给前端
        print("Progress:", log)

    trainer = Trainer(model_factory.create_training_components(), progress_callback=progress_update)
    result = trainer.train()
    return result


if __name__ == '__main__':
    handle_train_request()
