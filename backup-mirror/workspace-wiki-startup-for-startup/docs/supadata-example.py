from supadata import Supadata

supadata = Supadata(api_key="sd_e7bdebb82d0509439fdde5946d793e7f")

result = supadata.transcript(
    url="https://youtu.be/dQw4w9WgXcQ",
    lang="iw",
    mode="auto",
)

print(result)
