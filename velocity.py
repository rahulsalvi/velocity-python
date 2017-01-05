import sys
import os
import subprocess
import shlex
import datetime
import argparse
from enum import Enum

theme = os.getenv("BACKGROUND")
encoding = sys.getdefaultencoding()

class Format:
    class Code(Enum):
        black   = 0
        red     = 1
        green   = 2
        yellow  = 3
        blue    = 4
        magenta = 5
        cyan    = 6
        white   = 7
        default = 9
    def __init__(self, fg, bg):
        self.fg = fg
        self.bg = bg
        self.fgval = self.Code[self.fg.replace("bright", "")].value + 30
        self.bgval = self.Code[self.bg.replace("bright", "")].value + 40
        if self.fg[:6] == "bright":
            self.fgval += 60
        if self.bg[:6] == "bright":
            self.bgval += 60
    def getEscapeSequence(self):
        return "%{\033["+str(self.fgval)+";"+str(self.bgval)+"m%}"
    def getTmuxSequence(self):
        return "#[fg="+self.fg+"]#[bg="+self.bg+"]"

class Segment:
    def __init__(self, text, fmt):
        self.text = " " + text + " "
        self.fmt = fmt
    def getString(self, nextfmt, backwards):
        if backwards:
            if nextfmt == None:
                bg = "107" if theme == "light" else "100"
                return "%{\033["+str(self.fmt.bgval-10)+";"+bg+"m%}"+'\ue0b2'+self.fmt.getEscapeSequence()+self.text
            else:
                if self.fmt.bgval == nextfmt.bgval:
                    fg = "97" if theme == "light" else "90"
                    return "%{\033["+fg+";"+str(nextfmt.bgval)+"m%}"+'\ue0b3'+self.fmt.getEscapeSequence()+self.text
                else:
                    return "%{\033["+str(self.fmt.bgval-10)+";"+str(nextfmt.bgval)+"m%}"+'\ue0b2'+self.fmt.getEscapeSequence()+self.text
        else:
            if nextfmt == None:
                bg = "107" if theme == "light" else "100"
                return self.fmt.getEscapeSequence()+self.text+"%{\033["+str(self.fmt.bgval-10)+";"+bg+"m%}"+'\ue0b0'+"%{\033[0m%}"
            else:
                if self.fmt.bgval == nextfmt.bgval:
                    fg = "97" if theme == "light" else "90"
                    return self.fmt.getEscapeSequence()+self.text+"%{\033["+fg+";"+str(nextfmt.bgval)+"m%}"+'\ue0b1'
                else:
                    return self.fmt.getEscapeSequence()+self.text+"%{\033["+str(self.fmt.bgval-10)+";"+str(nextfmt.bgval)+"m%}"+'\ue0b0'
    def getTmux(self, nextfmt, backwards):
        if backwards:
            if nextfmt == None:
                bg = "white" if theme == "light" else "black"
                return "#[fg="+self.fmt.bg+"]"+'\ue0b2'+self.fmt.getTmuxSequence()+self.text
            else:
                if self.fmt.bgval == nextfmt.bgval:
                    fg = "white" if theme == "light" else "black"
                    return "#[fg="+fg+"]"+'\ue0b3'+self.fmt.getTmuxSequence()+self.text
                else:
                    return "#[fg="+self.fmt.bg+"]"+'\ue0b2'+self.fmt.getTmuxSequence()+self.text
        else:
            if nextfmt == None:
                bg = "white" if theme == "light" else "black"
                return self.fmt.getTmuxSequence()+self.text+"#[fg="+self.fmt.bg+"]#[bg="+bg+"]"+'\ue0b0'+"#[default]"
            else:
                if self.fmt.bgval == nextfmt.bgval:
                    fg = "white" if theme == "light" else "black"
                    return self.fmt.getTmuxSequence()+self.text+"#[fg="+fg+"]#[bg="+nextfmt.bg+"]"+'\ue0b1'
                else:
                    return self.fmt.getTmuxSequence()+self.text+"#[fg="+self.fmt.bg+"]#[bg="+nextfmt.bg+"]"+'\ue0b0'

def getTmuxOption(option, scope, default):
    value = subprocess.check_output(shlex.split("tmux show-options -qv"+scope+" "+option)).decode(encoding).rstrip()
    return default if not value else value

def setTmuxOption(option, scope, value):
    subprocess.Popen(shlex.split("tmux set -"+scope+" "+option+" "+value))

def resolve(segments, backwards):
    string = ""
    if backwards:
        string += segments[0].getString(None, backwards)
        for i in range(1, len(segments)):
            string += segments[i].getString(segments[i-1].fmt, backwards)
        return string
    else:
        for i in range(len(segments)-1):
            string += segments[i].getString(segments[i+1].fmt, backwards)
        string += segments[-1].getString(None, backwards)
        return string + " "

def resolveTmux(segments, backwards):
    string = ""
    if backwards:
        string += segments[0].getTmux(None, backwards)
        for i in range(1, len(segments)):
            string += segments[i].getTmux(segments[i-1].fmt, backwards)
        return string
    else:
        for i in range(len(segments)-1):
            string += segments[i].getTmux(segments[i+1].fmt, backwards)
        string += segments[-1].getTmux(None, backwards)
        return string + " "

def getHostText():
    username = os.getlogin()
    hostname = os.uname()[1]
    return username + "@" + hostname

def getDirectoryText():
    return os.getcwd().replace("/Users/rahulsalvi", "~", 1)

def getGitInfo(isInDotGitFolder):
    cmd = subprocess.Popen(['git', 'symbolic-ref', '-q', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = cmd.communicate()
    if 'fatal: Not' in err.decode(encoding):
        return "", -1
    elif not out:
        sha = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])
        return '\u27a6'+" "+sha.decode(encoding).rstrip(), 2
    else:
        if isInDotGitFolder:
            return ".git", 0
        changes = subprocess.check_output(['git', 'status', '--porcelain'])
        if not changes:
            return '\ue0a0'+" "+out.decode(encoding).replace("refs/heads/", "", 1).rstrip(), 0
        else:
            if "??" in changes.decode(encoding):
                return '\ue0a0'+" "+out.decode(encoding).replace("refs/heads/", "", 1).rstrip()+" \u00b1", 1
            else:
                return '\ue0a0'+" "+out.decode(encoding).replace("refs/heads/", "", 1).rstrip(), 1

def getBatteryInfo():
    out  = subprocess.check_output(shlex.split("pmset -g batt")).decode(encoding)
    try:
        line = out.split("\t")[1]
    except:
        return ""
    line = line.split("%")[0]
    if "AC" in out:
        return "Charging: ", line
    return "Battery: ", line

def getDateText():
    now = datetime.datetime.now()
    return now.strftime("%a %m/%d/%Y %I:%M %p")

def getShortDateText():
    now = datetime.datetime.now()
    return now.strftime("%I:%M %p")

def getSpotifyInfo():
    state       = subprocess.check_output(shlex.split("osascript -e 'tell application \"Spotify\" to return player state as string'"))
    name        = subprocess.check_output(shlex.split("osascript -e 'tell application \"Spotify\" to return name of current track as string'"))
    artist      = subprocess.check_output(shlex.split("osascript -e 'tell application \"Spotify\" to return artist of current track as string'"))

    state       = state.decode(encoding).rstrip()
    name        = name.decode(encoding).rstrip()
    artist      = artist.decode(encoding).rstrip()

    fieldLength = int(getTmuxOption("@SPOTIFYFIELDLENGTH", "g", "20"))
    name        = name[:fieldLength-2]+".." if len(name) > fieldLength else name
    artist      = artist[:fieldLength-2]+".." if len(artist) > fieldLength else artist
    return name + " - " + artist, state

def getSongTickText():
    tick = int(subprocess.check_output(shlex.split("osascript -e 'tell application \"Spotify\" to return player position / ((duration of current track) / 1000) * 10 as integer'")))
    string = "["
    for i in range(tick):
        string += "-"
    string += "|"
    for i in range(10 - tick):
        string += "-"
    string += "]"
    return string

def getProgressBarText(progress, tmux, filledFormat, emptyFormat, finalFormat):
    progressScaled = int(progress / 10)
    if tmux:
        string = filledFormat.getTmuxSequence()
    else:
        string = filledFormat.getEscapeSequence()
    for i in range(progressScaled):
        string += " "
    if tmux:
        string += emptyFormat.getTmuxSequence()
    else:
        string += emptyFormat.getEscapeSequence()
    for i in range(10-progressScaled):
        string += " "
    if tmux:
        string += finalFormat.getTmuxSequence()
    else:
        string += finalFormat.getEscapeSequence()
    return string

def promptMain():
    segments = []

    if theme == 'light':
        hostFormat        = Format('black', 'brightcyan')
        dirFormat         = Format('black', 'cyan')
        gitCleanFormat    = Format('black', 'green')
        gitDirtyFormat    = Format('black', 'yellow')
        gitDetachedFormat = Format('black', 'red')
    else:
        hostFormat        = Format('black', 'brightblue')
        dirFormat         = Format('black', 'blue')
        gitCleanFormat    = Format('black', 'green')
        gitDirtyFormat    = Format('black', 'yellow')
        gitDetachedFormat = Format('black', 'red')

    hostText           = getHostText()
    dirText            = getDirectoryText()
    gitText, gitStatus = getGitInfo(".git" in dirText)

    maxPromptPercent = os.getenv("MAXPROMPTSIZE", 33)
    maxPromptPercent = int(maxPromptPercent)/100
    maxPromptSize    = int(subprocess.check_output(['tput', 'cols'])) * maxPromptPercent

    if (len(hostText+dirText+gitText) < maxPromptSize) and (os.getenv("TMUX", "") == ""):
        segments.append(Segment(hostText, hostFormat))

    while (len(dirText+gitText) > maxPromptSize) and (dirText.count('/') > 1):
        dirs = dirText.split('/')
        dirText = "../" + '/'.join(dirs[2:])

    if os.getenv("NOSPLITDIRTEXT", False):
        segments.append(Segment(dirText, dirFormat))
    else:
        for directory in dirText.split('/'):
            segments.append(Segment(directory, dirFormat))

    if gitStatus == 0:
        segments.append(Segment(gitText, gitCleanFormat))
    elif gitStatus == 1:
        segments.append(Segment(gitText, gitDirtyFormat))
    elif gitStatus == 2:
        segments.append(Segment(gitText, gitDetachedFormat))

    sys.stdout.write(resolve(segments, False))

def tmuxStatusRightMain():
    segments = []

    if getTmuxOption("@STATUSRIGHTAUTOSCALE", "g", "false") == "true":
        width      = int(subprocess.check_output(shlex.split("tmux display-message -p \"#{window_width}\"")).decode(encoding).rstrip())
        baseCutoff = int(getTmuxOption("@AUTOSCALECUTOFF", "g", "150"))
        segmentFlags = ["false" for i in range(4)]
        if width < baseCutoff:
            segmentFlags[0] = "true"
            if width < (baseCutoff-15):
                segmentFlags[1] = "true"
                if width < (baseCutoff-30):
                    segmentFlags[2] = "true"
                    if width < (baseCutoff-75):
                        segmentFlags[3] = "true"
        setTmuxOption("@NOSONGTICK", "g", segmentFlags[0])
        setTmuxOption("@SHORTDATE", "g", segmentFlags[1])
        setTmuxOption("@NOSPOTIFY", "g", segmentFlags[2])
        setTmuxOption("@NOBATTERY", "g", segmentFlags[3])

    segments.append(Segment("PREFIX,}", Format('white', 'red')))
    segments.append(Segment("#{pane_current_command}", Format('black', 'brightmagenta')))

    if not getTmuxOption("@NOBATTERY", "g", "") == "true":
        batteryInfo = getBatteryInfo()
        if not batteryInfo == "":
            batteryAmt  = int(batteryInfo[1])
            if batteryAmt < 20:
                segments.append(Segment(batteryInfo[0]+batteryInfo[1]+"%", Format('black', 'red')))
            elif batteryAmt < 100:
                segments.append(Segment(batteryInfo[0]+batteryInfo[1]+"%", Format('black', 'yellow')))
            else:
                segments.append(Segment((batteryInfo[0] if batteryInfo[0] == "Battery: " else "Charged: ")+batteryInfo[1]+"%", Format('black', 'green')))

    if not getTmuxOption("@NOSPOTIFY", "g", "") == "true":
        spotifyInfo = getSpotifyInfo()
        if spotifyInfo[1] == "playing":
            segments.append(Segment(spotifyInfo[0], Format('black', 'brightgreen')))
            if not getTmuxOption("@NOSONGTICK", "g", "") == "true":
                segments.append(Segment(getSongTickText(), Format('black', 'brightgreen')))

    if getTmuxOption("@SHORTDATE", "g", "") == "true":
        segments.append(Segment(getShortDateText(), Format('black', 'brightyellow')))
    else:
        segments.append(Segment(getDateText(), Format('black', 'brightyellow')))

    sys.stdout.write("#{?client_prefix,"+resolveTmux(segments, True))

def tmuxStatusLeftMain():
    segments = []

    if theme == 'light':
        sessionFormat = Format('black', 'cyan')
    else:
        sessionFormat = Format('black', 'blue')

    segments.append(Segment(getHostText(), Format('black', 'brightblue')))
    segments.append(Segment("#{client_session}", sessionFormat))
    sys.stdout.write(resolveTmux(segments, False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("what", help="which prompt to show")
    args = parser.parse_args()
    if args.what == "PROMPT":
        promptMain()
    elif args.what == "TMUXSTATUSRIGHT":
        tmuxStatusRightMain()
    elif args.what == "TMUXSTATUSLEFT":
        tmuxStatusLeftMain()
    else:
        sys.stdout.write("UNKNOWN")
