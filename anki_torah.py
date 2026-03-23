from anki_torah.sefaria import SefariaClient, SefariaConfig

client = SefariaClient(SefariaConfig())

# print(client.get_english_text("Genesis 1:1"))
data = client.get_text_json_v1("Genesis 1:1")
print("versionTitle:", data.get("versionTitle"))
print("text:", client.get_english_text("Genesis 1:1"))

# print(len(client.get_text_range("Genesis 1:1-5")))
