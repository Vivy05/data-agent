from pathlib import Path
from typing import TypeVar, Type
from omegaconf import OmegaConf

T = TypeVar('T')

def load_config(config_path: Path,config_cls: Type[T]) -> T:
    context = OmegaConf.load(config_path)
    schema = OmegaConf.structured(config_cls)
    return OmegaConf.to_object(OmegaConf.merge(schema, context))