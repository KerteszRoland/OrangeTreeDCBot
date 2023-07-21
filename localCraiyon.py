import os
from craiyon import Craiyon
import pathlib


async def craiyon_generate(prompt):
    generator = Craiyon()
    result = await generator.async_generate(prompt)
    await result.async_save_images()
    image_paths = [filepath.absolute() for filepath in pathlib.Path("generated").glob('**/*')]
    
    return image_paths
