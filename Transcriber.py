import json
import os
import re

# Function to parse settings from Settings.json
def parse_settings():
    with open("Settings.json", "r") as settings_file:
        settings = json.load(settings_file)
    return settings

# Function to convert transcript lines to Lua format
def convert_lines(lines, settings):
    emoji_codes = {
        "😠": "ANG+0.2", # Max 100
        "😟": "STS+0.2",
        "🙂": "STS-0.2",
        "😊": "UHP-0.2",
        "😭": "UHP+0.2",
        "💤": "FAT+0.2",
        "🏃": "FAT-0.2",
        "🍽️": "HUN+0.2",
        "🤢": "SIC+0.2", 
        "😱": "PAN+0.2", # Max 100
        "😨": "FEA+0.2", 
        "👻": "LFT+0.2", #Light Footed
        "🔨": "CRP+0.2", #carpentry
        "🍳": "COO+0.2", #cooking
        "🎣": "FIS+0.2",
        "🚜": "FRM+0.2",
        "🍄": "FOR+0.2", #foraging
        "🐀": "TRA+0.2", #Trapping
        "🔫": "AIM+0.2",
        "🚗": "MEC+0.2",
        "🥈": "MTL+0.2", #metalworking
        "🏥": "DOC+0.2",
        "🧵": "TAI+0.2",
        "⚡": "ELC+0.2",
        "⚾": "BUA+0.2", #Blunt weapons somehow? lol
        "🔪": "SBA+0.2" #Short blade
    }


    converted_lines = []
    for line in lines:
        # Extract character speaking from the start of the line up to the colon
        colon_index = line["text"].find(":")
        if colon_index != -1:
            character = line["text"][:colon_index].strip()
            dialogue = line["text"][colon_index + 1:].strip()
        else:
            character = None
            dialogue = line["text"]
        # Map character to color and remove character from dialogue
        if character:
            color = settings.get(character.upper(), [1.0, 1.0, 1.0])
            dialogue = dialogue.replace(character + ":", "").strip()
        else:
            color = [1.0, 1.0, 1.0]

        # Convert emojis to specific codes
        dialogue = dialogue.replace("🎵", "[img=music]")

        # Initialize a dictionary to store the counts of each emoji code
        emoji_counts = {code: 0 for code in emoji_codes.values()}
        
        # Iterate over the dialogue to count emojis and aggregate codes
        codes = "BOR-0.2"  # Default code
        for emoji, code in emoji_codes.items():
            count = dialogue.count(emoji)
            if count > 0:
                emoji_counts[code] += count  # Aggregate counts
                # Remove emoji from dialogue
                dialogue = dialogue.replace(emoji, "")
        
        # Generate the combined emoji codes string
        emoji_code_str = ""
        for code, count in emoji_counts.items():
            if count > 0:
                # Parse the number past the operator, multiply it by the count, and concatenate it back with the code
                operator_index = code.find("+")
                if operator_index == -1:
                    operator_index = code.find("-")
                if operator_index != -1:
                    base_code = code[:operator_index]
                    number = float(code[operator_index + 1:])
                    multiplied_number = number * count
                    emoji_code_str += f"{base_code}{code[operator_index]}{multiplied_number},"

        # Remove trailing comma
        emoji_code_str = emoji_code_str.rstrip(",")
        codes += f",{emoji_code_str}" if emoji_code_str else ""

        # Split long lines into multiple sentences
        sentences = re.split(r'(?<!\d\.\d)(?<![A-Z]\.)(?<![A-Z][a-z]\.)(?<!\w\.\w)(?<=\.|\?|!)\s', dialogue)
        for sentence in sentences:
            converted_lines.append({"text": sentence.strip(), "color": color, "codes": codes})
    return converted_lines

# Function to parse transcript lines with character speaking and dialogue
def parse_transcript_line(line, settings, characters_spoken):
    colon_index = line.find(":")
    oc_index = line.find("[OC]")
    ov_index = line.find("[on viewscreen]")
    om_index = line.find("[on monitor]")
    
    # Check if line starts with '('
    if line.startswith("("):
        character = "NARRATOR"
        dialogue = line.strip()
    elif om_index != -1:
        character = line[:om_index].strip()
        dialogue = line[om_index + len("[on monitor]"):].replace(":", ": (On monitor)").strip()
    elif oc_index != -1:
        character = line[:oc_index].strip()
        dialogue = line[oc_index + len("[OC]"):].replace(":", ": (Offscreen)").strip()
    elif ov_index != -1:
        character = line[:ov_index].strip()
        dialogue = line[ov_index + len("[on viewscreen]"):].replace(":", ": (On viewscreen)").strip()
    elif colon_index != -1:
        character = line[:colon_index].strip()
        dialogue = line[colon_index + 1:].strip()
    else:
        character = "DEFAULT"  # Set a default character if not found
        dialogue = line.strip()
    
    # Exclude DEFAULT and NARRATOR characters from being considered as the first appearance in the episode
    if character not in ["DEFAULT", "NARRATOR"] and character not in characters_spoken:
        dialogue = f"({character}) {dialogue}"
        characters_spoken.add(character)
    
    return character, dialogue

# Function to create Lua data structure and write to Generated.lua
def create_lua_data(transcripts, settings):
    lua_data = "-- Generated Recorded Media Data File\n"
    lua_data += "RecMedia = RecMedia or {}\n\n"
    
    for transcript_name, transcript_data in transcripts.items():
        lua_data += f'-- {transcript_data["title"]}\n'
        lua_data += f'RecMedia["{transcript_name}"] = {{\n'
        lua_data += f'\titemDisplayName = "VHS: {transcript_data["itemDisplayName"]}",\n'
        lua_data += f'\ttitle = "{transcript_data["title"]}",\n'
        lua_data += f'\tsubtitle = {transcript_data.get("subtitle", "nil")},\n'
        lua_data += f'\tauthor = {transcript_data.get("author", "nil")},\n'
        lua_data += f'\textra = {transcript_data.get("extra", "nil")},\n'
        lua_data += f'\tspawning = 0,\n'
        lua_data += f'\tcategory = "Retail-VHS",\n'
        lua_data += '\tlines = {\n'
        for line in transcript_data["lines"]:
            if line["text"]:  # Skip empty lines
                lua_data += f'\t\t{{ text = "{line["text"]}", r = {line["color"][0]}, g = {line["color"][1]}, b = {line["color"][2]}, codes = "{line["codes"]}" }},\n'
        lua_data += '\t},\n'
        lua_data += '};\n\n'
    
    with open("Generated.lua", "w") as lua_file:
        lua_file.write(lua_data)

# Main function
def main():
    settings = parse_settings()
    transcripts = {}
    transcripts_folder = "Transcripts"
    
    # Parse each transcript file
    for filename in os.listdir(transcripts_folder):
        if filename.endswith(".txt"):
            transcript_name = os.path.splitext(filename)[0]
            with open(os.path.join(transcripts_folder, filename), "r", encoding="utf-8") as transcript_file:
                # Read the first four lines for title and itemDisplayName
                title_lines = [transcript_file.readline().strip() for _ in range(4)]
                item_display_name = title_lines[0]
                title = title_lines[1] + " - " + title_lines[2]

                # Read the rest of the lines for dialogue
                lines = []
                characters_spoken = set()  # Initialize set to keep track of characters spoken
                for line in transcript_file.readlines():
                    character, dialogue = parse_transcript_line(line, settings, characters_spoken)
                    if dialogue:  # Skip empty lines
                        converted_lines = convert_lines([{"text": dialogue}], settings)  # Convert the line
                        color = settings.get(character.upper(), settings.get("DEFAULT", [1.0, 1.0, 1.0]))
                        lines.extend({"text": line["text"], "color": color, "codes": line["codes"]} for line in converted_lines)
                transcripts[transcript_name] = {"title": title, "itemDisplayName": item_display_name, "lines": lines}
    
    create_lua_data(transcripts, settings)
    print("Generated.lua file has been created successfully.")

if __name__ == "__main__":
    main()