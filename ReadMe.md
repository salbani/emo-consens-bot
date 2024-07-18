# Add .env

Add the file bot_system/.env with the contents:

```
OPENAI_API_KEY = "your openai api key"
```

# install requirements 

It is advised to setup a local virtual python environment. Look [here](https://docs.python.org/3/library/venv.html).

`pip install -r requirements.txt`

# Run the system
Run `python bot_system/main.py`

# Show debug info
To show additional debug information (face analysis visualization and speech intend plotting) add the debug argument to the main when initilizing PepperGPT


```python
prompter = PepperGPT(mute=False, no_cost=False, no_pepper=True, debug=True, context_data_path="bot_system/data")
```