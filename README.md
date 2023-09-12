This is the repository for the demo code used during the presentation
for [II. PE-ZEK E-sport Szakmai Napok](https://zek.uni-pannon.hu/index.php/hu/hirek-es-esemenyek-2/ii-pe-zek-e-sport-szakmai-napok-2023.html)
.

# How to run this code

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python (version 3.x+)
- pip (version 21.X+)

### Setting up the Python Virtual Environment

1. Clone this repository
2. Open a terminal/command prompt.
3. Navigate to the root directory of your project.

```bash
cd /path/to/your/project
```

4. Create a virtual environment (venv). Replace `venv` with your preferred virtual environment name.

```bash
python -m venv venv
```

5. Activate the virtual environment:

    - On Windows:

   ```bash
   venv\Scripts\activate
   ```

    - On macOS and Linux:

   ```bash
   source venv/bin/activate
   ```
6. Copy `.env.example` to `.env`. See additional information.

### Installing Project Dependencies

While inside the activated virtual environment, use `pip` to install the project's dependencies listed
in `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Running the Application

Now that you have set up the virtual environment and installed the dependencies, you can run the different files of the
application.

Eg:

```bash
python 01_simple_approach.py
```

## Additional Information

In case you want to use your own account, change `.env` values to live ones.

You can get a Riot API key here: https://developer.riotgames.com.

Don't forget to change the Riot server names in the code of `src/riot_api.py` to your own account region.

## License

MIT