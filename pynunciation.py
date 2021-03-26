from google_speech import Speech
from unidecode import unidecode
import argparse
import re
import requests
from io import BytesIO

# you can also apply audio effects while playing (using SoX)
# see http://sox.sourceforge.net/sox.html#EFFECTS for full effect documentation
# speech.play(sox_effects)
sox_effects = ("speed", "1")


def output_text(word, lang):
    word = unidecode(word)
    return f"{lang.upper()}_{word.lower().replace(' ', '_')}"


def download_audio_leo(audio_code, cookies=None):
    try:
        # if we are doing this without cookies, we make a random request to get some
        if not cookies:
            resp = requests.get("https://dict.leo.org/")
            cookies = resp.cookies

        # audio code we find at the 'data-dz-rel-audio' component in the buttom class that plays the audio in LEO
        resp = requests.get(url=f'https://dict.leo.org/media/audio/{audio_code}.ogg', cookies=cookies)
        
        if resp.content:
            return BytesIO(resp.content)
        else:
            return None

    except Exception as e:
        print(f"An error occurred while getting the data from LEO. {str(e)}")
        return None


def get_from_leo(word, lang):
    url = f"https://dict.leo.org/englisch-deutsch/{word}"

    try:
        resp1 = requests.get(url)

        # these are the audio paths in the LEO API. It is ordered in pairs, so the first two are:
        # (translation 1 english word audio)[0] -> (translation 1 german word audio)[1]
        # (translation 2 english word audio)[2] -> (translation 2 german word audio)[3]
        # (translation 3 english word audio)[4] -> (translation 3 german word audio)[5]
        # and so on...
        # we normally will want the first sound in german, so [1]

        audio_codes = re.findall(r"(?s)(?<=icon noselect icon_play-circle-outline icon_size_18  darkgray).*?(?=data-dz-rel-audio)data-dz-rel-audio=\"(.*?)\"", resp1.text)

        content = download_audio_leo(audio_code=audio_codes[1], cookies=resp1.cookies)

        if content:
            with open(f'{output_text(word, lang)}.mp3', 'wb') as f:
                f.write(content.read())

            return True
        else:
            return False

    except Exception as e:
        print(str(e))
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate and save a given word's speech.")
    parser.add_argument('--word', type=str, default=None, help='Word to be spoken')
    parser.add_argument('--leo_code', type=str, default=None, help='LEO audio code if you really want the audio from there and the script magic is not working. If the --word argument is given, the output name format will be preserved, otherwise you will get a random_leters.mp3 in your folder.')
    parser.add_argument('--lang', type=str, default='de', help='Language that you want your text to be spoken. Until it does not make any difference besides changing the name of the outputted file.')
    parser.add_argument('--force_google', type=bool, default=False, help='It forces using Google Translate engine (useful when LEO fails to work (aka do wrong stuff))')

    args = parser.parse_args()

    if not args.word and not args.leo_code:
        print("--word or --leo_code have to be provided as argument!")
        exit(1)

    if args.leo_code:
        audio = download_audio_leo(audio_code=args.leo_code)
        output_file = output_text(args.word, args.lang) if args.word else args.leo_code
        with open(f'{output_file}.mp3', 'wb') as f:
            f.write(audio.read())

        print("You forced, but i think LEO worked, check it out! :-)")

    # we try first with LEO, if we dont find anything there, then we use google translate
    elif not get_from_leo(args.word, args.lang) or args.force_google:
        print("We are getting from Google Translate anyways... :-(")
        speech = Speech(args.word, args.lang)
        # save the speech to an MP3 file (no effect is applied)
        speech.save(f"{output_text(args.word, args.lang)}.mp3")
    
    else:
        print("Apparently LEO worked, check it out! :-)")


if __name__ == "__main__":
    main()

