
mock_data = [
  "https://cdn.discordapp.com/attachments/950813918350180402/950857787007729724/unknown.png",
  "https://cdn.discordapp.com/attachments/603796374982754304/948050557946454126/unknown.png",
  "https://cdn.discordapp.com/attachments/603796374982754304/947032437274320906/unknown.png",
  "https://cdn.discordapp.com/attachments/603796374982754304/943924296772911144/unknown.png",
  "https://cdn.discordapp.com/attachments/795549507588063252/943540742163415060/IMG_8588.jpg",
  "https://preview.redd.it/swsqeffnidm81.jpg?width=640&crop=smart&auto=webp&s=5aa611521c339731fe1e6d1d808f5f8f15fa13c4",
  "https://i.redd.it/6s96i19r8bm81.jpg"
]

makers_mock_data = [
  {"name": "Marshmallowww", "subs": 23},
  {"name": "John420", "subs": 20},
  {"name": "CloudyWithAChanceOfMeatballs", "subs": 21}
]

# get latest/trending? memes
def get_memes():
  return mock_data

def get_meme_url(meme_id):
  return mock_data[meme_id]

def get_makers():
  return makers_mock_data

def get_makers_memes(username):
  return mock_data[3:]