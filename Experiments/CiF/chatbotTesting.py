import ollama



speaker = False
initialize = True
conversationLog = ["",""]

client = ollama.Client(host="http://localhost:11434")
for i in range(1):
    speaker = not speaker
    if not initialize:
        if speaker:
            conversationLog[0] += "\n You: " + stream['message']['content']
            conversationLog[1] += "\n Stranger: " + stream['message']['content'] # For the initial speaker
            prompt = "You are conversing with a stranger, what do you say? Don't use brackets or options in your response. Act as if you're the one speaking. Below is the conversation log: " + conversationLog[1]
        else:
            conversationLog[0] += "\n Stranger: " + stream['message']['content'] # For the second speaker
            conversationLog[1] += "\n You: " + stream['message']['content']
            prompt = "You are conversing with a stranger, what do you say? Don't use brackets or options in your response. Act as if you're the one speaking. Below is the conversation log: " + conversationLog[0]
    else:
        prompt = "<|system|>Enter RP mode. Pretend to be Fred whose persona follows: Fred is a nasty old curmudgeon. He has been used and abused, at least in his mind he has. And so he isn't going to take anything from anyone. He does get excited about his kids even though they never see him, and about when he met his wife. but that's it. He's nasty, but he will never swear unless he is really provoked."


    stream = client.chat(model='vthebeast/mythalion-13b', messages=[{'role': 'user', 'content': prompt}])
    initialize = False

    print(stream['message']['content'], end='', flush=True)

conversationLog[0] = stream["message"]["content"]
print(conversationLog)


