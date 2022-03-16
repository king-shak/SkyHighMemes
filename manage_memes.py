
mock_data = [
  "https://cdn.discordapp.com/attachments/828079037565108265/953530540135424071/unknown.png",
  "https://cdn.discordapp.com/attachments/940733112692932668/950201782297034752/Screen_Shot_2020-10-05_at_11.png",
  "https://cdn.discordapp.com/attachments/828079037565108265/953530905387999232/unknown.png",
  "https://media.discordapp.net/attachments/828079037565108265/953531153858576394/unknown.png",
  "https://cdn.discordapp.com/attachments/828079037565108265/953531433341845594/unknown.png",
  "https://cdn.discordapp.com/attachments/828079037565108265/953532727246868550/download.gif",
  "https://cdn.discordapp.com/attachments/948007526815920233/953538749243998218/Macaca_nigra_self-portrait__rotated_and_cropped_.0.jpg",
  "https://cdn.discordapp.com/attachments/828079037565108265/953539068455714816/unknown.png",
  "https://cdn.discordapp.com/attachments/828079037565108265/953539307275186206/unknown.png",
  "https://cdn.discordapp.com/attachments/828079037565108265/953539677451866112/unknown.png",
  "https://cdn.discordapp.com/attachments/828079037565108265/953540703827410974/unknown.png",
  "https://cdn.discordapp.com/attachments/828079037565108265/953541429572010014/unknown.png",
  "https://c.tenor.com/Jt2hUuHic60AAAAM/denzel-washington-my-heart.gif"
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
