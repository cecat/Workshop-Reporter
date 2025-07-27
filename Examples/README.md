# Simple LLM Example

This folder contains a very basic example of how to call LLMs from Python. It's designed to be easy to understand and modify.

## Files

- **`chat.py`** - Main Python script that sends a prompt to OpenAI and prints the response
- **`secrets_template.yml`** - Template file showing proper format for your API key
- **`secrets.yml`** - Where you put your OpenAI API key (create from template, keep private!)
- **`config.py`** - Configuration settings like which model to use
- **`prompt.yml`** - The text prompt you want to send to the LLM
- **`requirements.txt`** - List of Python packages needed for this example

## Complete Setup for Beginners (macOS)

### Step 1: Open Terminal
- Press `Command + Space` to open Spotlight
- Type "Terminal" and press Enter
- You should see a window with a command prompt

### Step 2: Navigate to the Examples folder
```bash
# Change to the Examples directory
cd path/to/Workshop-Reporter/Examples
```
*Replace `path/to/Workshop-Reporter` with the actual path to your project*

### Step 3: Set up Python environment (recommended)
```bash
# Create a new conda environment (if you have conda installed)
conda create -n workshop-reporter python=3.9
conda activate workshop-reporter

# OR if you prefer using Python's built-in venv:
# python3 -m venv workshop-env
# source workshop-env/bin/activate
```

### Step 4: Install required packages
```bash
# Install packages from requirements.txt
pip install -r requirements.txt

# OR install manually:
# pip install openai pyyaml
```

### Step 5: Get an OpenAI API key
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in to your OpenAI account
3. Click "Create new secret key"
4. Copy the key (it starts with `sk-`)
5. **Important:** Save this key somewhere safe - you won't be able to see it again!

### Step 6: Create and Add your API key
1. Copy `secrets_template.yml` to `secrets.yml`
   ```bash
   cp secrets_template.yml secrets.yml
   ```
2. Open `secrets.yml` in a text editor:
   ```bash
   # Using nano (simple terminal editor):
   nano secrets.yml

   # OR using TextEdit (macOS default):
   open -a TextEdit secrets.yml

   # OR using VS Code (if installed):
   code secrets.yml
   ```
3. Choose one format for your API key:
   - **Nested format (recommended):**
     ```yaml
     openai:
       api_key: your-api-key-here
     ```
   - **Flat format (alternative):**
     ```yaml
     openai_api_key: your-api-key-here
     ```
4. Replace `your-api-key-here` with your actual OpenAI API key
5. Save the file (in nano: `Control+X`, then `Y`, then `Enter`)

### Step 7: Run the example
```bash
python chat.py
```

You should see output like:
```
🤖 Simple LLM Chat Example
========================================
Loading configuration...
Using model: gpt-4o-mini
Prompt: Once upon a time, in a land far away, there was a magical...

Sending request to LLM...
----------------------------------------
🤖 LLM Response:
[AI generated story will appear here]
----------------------------------------
Done!
```

## Customizing

### Change the prompt
Edit `prompt.yml` and replace the text with whatever you want to ask the LLM.

### Change the model
Edit `config.py` and modify the `model` field. Options include:
- `gpt-4o-mini` (recommended for development - good balance of cost and capability)
- `gpt-4o` (most capable but more expensive)
- `gpt-3.5-turbo` (faster and cheaper)

### Adjust response settings
In `config.py`, you can modify:
- `temperature` - Controls creativity (0.0 = very focused, 1.0 = very creative)
- `max_tokens` - Maximum length of response
- `timeout` - How long to wait for a response

## Security Note

**NEVER commit your `secrets.yml` file with a real API key to version control!**

The example `secrets.yml` contains a placeholder. Always keep your real API keys private.

## Troubleshooting

### Common Setup Issues
- **"python: command not found"** - You may need to use `python3` instead of `python`
- **"pip: command not found"** - Try `pip3` instead of `pip`, or install pip first
- **"conda: command not found"** - Conda isn't installed. Use the venv option instead:
  ```bash
  python3 -m venv workshop-env
  source workshop-env/bin/activate
  ```
- **"No such file or directory"** - Make sure you're in the correct directory. Use `pwd` to check your current location and `ls` to see files
- **Permission denied** - You might need to use `sudo pip install` (not recommended) or fix your Python installation

### API-Related Issues
- **"API key not found"** - Make sure you've added your real API key to `secrets.yml`
- **"Rate limit exceeded"** - You're sending requests too quickly. Wait a moment and try again
- **"Insufficient funds"** - You need to add credits to your OpenAI account at https://platform.openai.com/account/billing
- **"Invalid API key"** - Double-check that you copied the key correctly (it should start with `sk-`)

### Python Environment Issues
- **Import errors** - Make sure you've installed the required packages with `pip install -r requirements.txt`
- **"Module not found"** - Your virtual environment might not be activated, or packages weren't installed in the right environment

### Getting Help
If you're still stuck:
1. Check that you're in the right directory: `pwd` should show something ending in `/Examples`
2. Check that files exist: `ls` should show `chat.py`, `secrets.yml`, etc.
3. Check your Python version: `python --version` (should be 3.7 or higher)
4. Check installed packages: `pip list` should show `openai` and `PyYAML`

## What's Next?

Once you understand this basic example, you can:
- Modify it to read prompts from user input instead of files
- Add conversation history to maintain context
- Integrate it into the main Workshop Reporter project
- Experiment with different models and settings
