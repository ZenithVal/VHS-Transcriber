import json
import os

# Function to parse settings from Settings.json
def parse_settings():
    with open("Settings.json", "r") as settings_file:
        settings = json.load(settings_file)
    return settings

# Function to convert transcript lines to Lua format
def convert_lines(lines, settings):
    converted_lines = []
    for line in lines:
        text = line["text"]
        # Convert emojis to specific codes
        text = text.replace("🎵", "[img=music]")
        # Split long lines into multiple sentences
        while len(text) > 0:
            end_index = min(text.find("."), text.find("?"), text.find("!"))
            if end_index == -1:
                converted_lines.append(text)
                break
            converted_lines.append(text[:end_index + 1])
            text = text[end_index + 1:].strip()
    return converted_lines

# Function to create Lua data structure and write to Generated.lua
def create_lua_data(transcripts, settings):
    lua_data = "-- Generated Recorded Media Data File\n"
    lua_data += "RecMedia = RecMedia or {}\n\n"
    
    for transcript_name, transcript_data in transcripts.items():
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
            lua_data += f'\t\t{{ text = "{line["text"]}", r = {line["color"][0]}, g = {line["color"][1]}, b = {line["color"][2]}, codes = "{line["codes"]}" }},\n'
        lua_data += '\t}\n'
        lua_data += '}\n\n'
    
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
            with open(os.path.join(transcripts_folder, filename), "r") as transcript_file:
                # Read the first four lines for title and itemDisplayName
                title_lines = [transcript_file.readline().strip() for _ in range(4)]
                item_display_name = title_lines[0]
                title = title_lines[1] + " - " + title_lines[2]

                # Read the rest of the lines for dialogue
                lines = [{"text": line.strip(), "color": settings.get(line.split(":")[0], [1.0, 1.0, 1.0]), "codes": "BOR-1"} for line in transcript_file.readlines() if line.strip()]
                converted_lines = convert_lines(lines, settings)
                transcripts[transcript_name] = {"title": title, "itemDisplayName": item_display_name, "lines": [{"text": line, "color": [1.0, 1.0, 1.0], "codes": "BOR-1"} for line in converted_lines]}
    
    create_lua_data(transcripts, settings)
    print("Generated.lua file has been created successfully.")

if __name__ == "__main__":
    main()