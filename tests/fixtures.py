# -*- coding: utf-8 -*-
from io import BytesIO
import os
import shutil

from PIL import Image
import pytest

TMP_FILE_PATH = "/tmp/example.png"


@pytest.fixture
def generated_file(scope="session") -> BytesIO:
    file = BytesIO()
    image = Image.new("RGBA", size=(1000, 1000), color=(0, 0, 0))
    image.save(file, "png")
    yield file
    file.close()


@pytest.fixture
def file_length(generated_file) -> int:
    return generated_file.getbuffer().nbytes


@pytest.fixture
def file(generated_file) -> BytesIO:
    generated_file.seek(0)
    yield generated_file


@pytest.fixture
def local_file_path(generated_file) -> str:
    with open(TMP_FILE_PATH, "wb") as f:
        shutil.copyfileobj(generated_file, f, length=131072)
    yield TMP_FILE_PATH
    os.remove(TMP_FILE_PATH)
