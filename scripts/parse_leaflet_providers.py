"""
Script to parse the tile providers defined by the leaflet-providers.js
extension to Leaflet (https://github.com/leaflet-extras/leaflet-providers).

It accesses the defined TileLayer.Providers objects through javascript
using Selenium as JSON, and then processes this a fully specified
javascript-independent dictionary and saves that final result as a JSON file.

"""
import json
import os
import tempfile

import selenium.webdriver
import git


GIT_URL = "https://github.com/leaflet-extras/leaflet-providers.git"


def get_json_data():
    with tempfile.TemporaryDirectory() as tmpdirname:
        repo = git.Repo.clone_from(GIT_URL, tmpdirname)
        commit_hexsha = repo.head.object.hexsha
        commit_message = repo.head.object.message

        index_path = "file://" + os.path.join(tmpdirname, 'index.html')

        driver = selenium.webdriver.Firefox()
        driver.get(index_path)
        data = driver.execute_script(
            'return JSON.stringify(L.TileLayer.Provider.providers)')
        driver.close()

    data = json.loads(data)
    description = "commit {0} ({1})".format(
        commit_hexsha, commit_message.strip())

    return data, description


def process_provider(data, name='OpenStreetMap'):
    provider = data[name].copy()
    variants = provider.pop('variants', None)
    options = provider.pop('options')
    provider_keys = {**provider, **options}

    if variants is None:
        provider_keys['name'] = name
        return provider_keys

    result = {}

    for variant in variants:
        var = variants[variant]
        if isinstance(var, str):
            variant_keys = {'variant': var}
        else:
            variant_keys = var.copy()
            variant_options = variant_keys.pop('options', {})
            variant_keys = {**variant_keys, **variant_options}
        variant_keys = {**provider_keys, **variant_keys}
        variant_keys['name'] = "{provider}.{variant}".format(
            provider=name, variant=variant)
        result[variant] = variant_keys

    return result


def process_data(data):
    result = {}
    for provider in data:
        result[provider] = process_provider(data, provider)
    return result


if __name__ == "__main__":
    data, description = get_json_data()
    result = process_data(data)
    with open("leaflet-providers-parsed.json", "w") as f:
        # wanted to add this as header to the file, but JSON does not support
        # comments
        print("JSON representation of the leaflet providers defined by the "
              "leaflet-providers.js extension to Leaflet "
              "(https://github.com/leaflet-extras/leaflet-providers)")
        print("This file is automatically generated from {}".format(
            description))
        json.dump(result, f)
