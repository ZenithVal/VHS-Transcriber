import json
import os
import re

# Function to parse settings from Settings.json
def parse_settings():
    with open("Settings.json", "r") as settings_file:
        settings = json.load(settings_file)
    return settings

# Function to convert transcript lines to Lua format
def convert_lines(lines, settings, borLine, expList):
    emoji_codes = {
        #Stats
        "😠": "ANG+0.2", # Anger+
        "❓": "ANG-0.2", # Anger-
        "❓": "BOR+0.2", # Boredom
        "❓": "BOR-0.2", # Boredom-
        "💤": "FAT+0.2", # Fatigue+
        "🏃": "FAT-0.2", # Fatigue-
        "🍽️": "HUN+0.2", # Hunger+
        "❓": "HUN-0.2", # Hunger-
        "😟": "STS+0.2", # Stress+
        "🙂": "STS-0.2", # Stress-
        "😨": "FEA+0.2", # Fear+
        "❓": "FEA-0.2", # Fear-
        "😱": "PAN+0.2", # Panic+ (Max 100)
        "❓": "PAN-0.2", # Panic-
        "❓": "SAN+0.2", # Sanity+
        "🤪": "SAN-0.2", # Sanity-
        "🤢": "SIC+0.1", # Sick+
        "❓": "SIC-0.1", # Sick-
        "❓": "PAI+0.2", # Pain+
        "❓": "PAI-0.2", # Pain-
        "🍺": "DRU+0.2", # Drunk+
        "❓": "DRU-0.2", # Drunk-
        "💧": "THI+0.2", # Thirst+
        "❓": "THI-0.2", # Thirst-
        "😭": "UHP+0.2", # Unhappiness+ (Makes u sadder)
        "😊": "UHP-0.2", # Unhappiness- 

        # Skills
        "👟": "SPR+0.4", # Sprinting
        "👻": "LFT+0.4", # Light Footed
        "💃": "NIM+0.4", # Nimble
        "🤫": "SNE+0.4", # Sneaking

        # Survival
        "🎣": "FIS+0.4", # Fishing
        "🐀": "TRA+0.4", # Trapping
        "🍄": "FOR+0.4", # foraging

        # Crafting
        "🔨": "CRP+0.4", # Carpentry
        "🍳": "COO+0.4", # Cooking
        "🚜": "FRM+0.4", # Farming
        "🏥": "DOC+0.4", # Medical
        "⚡": "ELC+0.4", # Electricity
        "🥈": "MTL+0.4", # Metalworking
        "🧵": "TAI+0.4", # Tailoring
        "🚗": "MEC+0.4", # Mechanic

        # Guns
        "🔫": "AIM+0.4", # Aiming
        "🔄": "REL+0.4", # Reloading

        # Melee
        "🪓": "BAA+0.4", # Axe
        "🔱": "SPE+0.4", # Spear
        "🔧": "SBU+0.4", # Short Blunt
        "⚾": "BUA+0.4", # Long Blunt
        "🔪": "SBA+0.4", # Short blade
        "🗡️": "LBA+0.4" # Long blade
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
        

        # List of Codes
        codes = []

        # Add BOR-0.2 if applicable
        if borLine == True:
            codes.append("BOR-0.5")

        # Iterate over the dialogue to count emojis and aggregate codes
        for emoji, code in emoji_codes.items():
            count = dialogue.count(emoji)
            if count > 0:
                emoji_counts[code] += count  # Aggregate counts
                # Remove emoji from dialogue
                dialogue = dialogue.replace(emoji, "")
        
        # Generate the combined emoji codes string
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
                    codes.append(f"{base_code}{code[operator_index]}{round(multiplied_number, 4)}")
                    
                    # Keep track of all the EXP from each source in the EXP list {}
                    if base_code in expList:
                        expList[base_code] += multiplied_number
                    else:
                        expList[base_code] = multiplied_number

        # Create a list seperated by commas for the codes, if any ()
        codesStr = ""
        if len(codes) > 0:
            codesStr = ",".join(codes)

        # Split long lines into multiple sentences
        sentences = re.split(r'(?<!\d\.\d)(?<![A-Z]\.)(?<![A-Z][a-z]\.)(?<!\w\.\w)(?<=\.|\?|!)\s', dialogue)
        for sentence in sentences:
            converted_lines.append({"text": sentence.strip(), "color": color, "codes": codesStr})
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

    # list for printing out the total EXP from each source
    expList = {}
    
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
                lineNumber = 0
                lineNextBOR = 0

                characters_spoken = set()  # Initialize set to keep track of characters spoken
                for line in transcript_file.readlines():
                    character, dialogue = parse_transcript_line(line, settings, characters_spoken)
                    if dialogue:  # Skip empty lines
                        # Check if the line is a BOR line
                        borLine = False
                        if lineNextBOR == lineNumber:
                            borLine = True
                            lineNextBOR += 15
                        lineNumber += 1

                        converted_lines = convert_lines([{"text": dialogue}], settings, borLine, expList)  # Convert the line

                        color = settings.get(character.upper(), settings.get("DEFAULT", [1.0, 1.0, 1.0]))
                        lines.extend({"text": line["text"], "color": color, "codes": line["codes"]} for line in converted_lines)
                transcripts[transcript_name] = {"title": title, "itemDisplayName": item_display_name, "lines": lines}
                print (f"{transcript_name} parsed.")

    # Print out the EXP list and their total values
    print("\nEXP List:")
    for key, value in expList.items():
        print(f"{key}: {round((value*16.666), 0)}")

    
    create_lua_data(transcripts, settings)
    print("Generated.lua file has been created successfully.")
    input("Press Enter to exit...")
    
if __name__ == "__main__":
    main()