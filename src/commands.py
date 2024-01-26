import interactions 
import datetime
import os
import src.Voice2Text as v2t

with open(r"src/token.txt", "r") as f:
    token = f.read()
client = interactions.Client(token = token)

voice_channel = None

PATH = "outputs"

scopes = [833275051208867841,1045965463575855124, 1196126269687996536]



@interactions.listen()
async def on_ready():
    if not os.path.exists(f"{PATH}"):
        os.mkdir(f"{PATH}")
    print('Bot start!')

@interactions.slash_command(name = "record", description = "Start recording.")
async def record(ctx: interactions.SlashContext):
    global voice_channel
    await ctx.defer()
    if voice_channel is not None:
        await ctx.send("Bot is already recording. Bot can only record one channel.", ephemeral=True)
        return
    if ctx.channel.type != 2:
        await ctx.send("Please use this command in voice channel", ephemeral=True)
        return
    voice_channel = await ctx.channel.connect()
    await voice_channel.start_recording(output_dir=PATH,encoding="wav")
    await ctx.send("Bot Start recording...")

@interactions.slash_command(name = "stop", description = "Stop recording.")
async def stop(ctx: interactions.SlashContext):
    global voice_channel
    await ctx.defer()
    if voice_channel is None:
        await ctx.send("Bot is not recording.", ephemeral=True)
        return
    await voice_channel.stop_recording()
    await ctx.send("Bot Stop recording.")
    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    files = voice_channel.recorder.output.values()
    await voice_channel.disconnect()
    voice_channel = None
    if not os.path.exists(f"{PATH}/{time}"):
        os.mkdir(f"{PATH}/{time}")
    ids = {}
    for i in files:
        id = i.split("_")[-1].split(".")[0]
        ids[id] = client.get_user(user_id = id).display_name
        os.rename(i, f"{PATH}/{time}/{id}.wav")
    with open(f"{PATH}/{time}/ids.txt", "w", encoding="utf8") as f:
        for i in ids:
            f.write(f"{i} {ids[i]}\n")

@interactions.slash_command(name = "list", description = "list latest 5 recording")
async def list(ctx: interactions.SlashContext):
    await ctx.defer()
    files = os.listdir(PATH)
    if len(files) == 0:
        await ctx.send("No recording found.")
        return
    files = sorted(files, key=lambda x:os.path.getmtime(f"{PATH}/"+x))
    files = [i for i in files if os.path.isdir(f"{PATH}/"+i)]
    files = files[-5:]
    #give a number to each file
    for i in range(len(files)):
        files[i] = f"{i+1}. {files[i]}"
    text = "\n".join(files)
    await ctx.send(text)

@interactions.slash_command(name = "transcribe", description = "Transcribe recording.")
@interactions.slash_option(
    name="number",
    description="You can get the number from /list, default is latest recording.",
    required=False,
    opt_type=interactions.OptionType.INTEGER
)
async def transcribe(ctx: interactions.SlashContext, number: int = 1):
    global voice_channel
    await ctx.defer()
    d = f"{PATH}/"
    targets = sorted([d+i for i in os.listdir(d)],key=os.path.getmtime)
    if number < 0 or number > 5:
        await ctx.send("Invalid Number.", ephemeral=True)
        return
    
    if number > len(targets):
        await ctx.send("Invalid Number.", ephemeral=True)
        return
    target = targets[-number]
    #simply send file if exists

    if os.path.exists(target+"/text.txt"):
        await ctx.send(file=interactions.File(target+"/text.txt", file_name=f"{target}.txt"))
        return
    ids = {}
    await ctx.send("Transcribing...")
    with open(target+"/ids.txt", "r", encoding="utf8") as f:
        for i in f.readlines():
            ids[i.split()[0]] = i.split()[1]
    text = {}
    for i in os.listdir(target):
        if i.endswith(".wav"):
            temp = v2t.transcribe(target+"/"+i)
            for j in temp:
                temp[j] = f"{ids[i.split('.')[0]]}: {temp[j]}"
            text.update(temp)
    with open(target+"/text.txt", "w", encoding="utf8") as f:
        for i in sorted(text, key=lambda x:float(x)):
            f.write(f"{text[i]}\n\n")
    await ctx.send(file=interactions.File(target+"/text.txt", file_name=f"{target}.txt"))
            

