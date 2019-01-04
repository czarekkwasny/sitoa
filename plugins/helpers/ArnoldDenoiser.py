"""************************************************************************************************************************************
Copyright 2017 Autodesk, Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. 
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, 
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
See the License for the specific language governing permissions and limitations under the License.
************************************************************************************************************************************"""

# Arnold Denoiser
# Initial code generated by Softimage SDK Wizard
# Executed Tue Dec 11 19:48:36 UTC+0100 2018 by Jens Lindgren

import win32com.client
from win32com.client import constants as C

import glob
import os
import re
import subprocess
import sys
import threading
from time import sleep

null = None
false = 0
true = 1

# startupinfo to prevent Windows processes to display a console window
if sys.platform == 'win32':
    _no_window = subprocess.STARTUPINFO()
    _no_window.dwFlags |= subprocess.STARTF_USESHOWWINDOW
else:
    _no_window = None


def XSILoadPlugin( in_reg ):
    if Application.plugins('Arnold Tools') is None:
        Application.LoadPlugin(XSIUtils.BuildPath(in_reg.OriginPath, 'ArnoldTools.js'))
   
    h = Application.SItoAToolHelper()
    h.SetPluginInfo(in_reg, 'Arnold Denoiser')

    in_reg.RegisterCommand('OpenDenoiserProperty', 'SITOA_OpenDenoiserProperty')
    in_reg.RegisterProperty('arnold_denoiser')
    #RegistrationInsertionPoint - do not remove this line

    return true

def XSIUnloadPlugin( in_reg ):
    return true

def OpenDenoiserProperty_Init( in_ctxt ):
    oCmd = in_ctxt.Source
    oArgs = oCmd.Arguments
    oArgs.Add("in_inspect")
    return true

def OpenDenoiserProperty_Execute(in_inspect):
    inspect = True if in_inspect is None else in_inspect

    obj = Application.ActiveSceneRoot
    obj = Application.ActiveProject.ActiveScene.ActivePass
    propCollection = obj.Properties
    prop = propCollection.find('arnold_denoiser')

    if not prop:
         prop = obj.AddProperty("arnold_denoiser", false, "Arnold Denoiser")
    
    if inspect:
        Application.InspectObj(prop)

    return prop

def arnold_denoiser_Define( in_ctxt ):
    cp = in_ctxt.Source
    cp.AddParameter2('input',               C.siString,                  '', None,       None, None, None, C.siClassifUnknown, C.siPersistable)
    cp.AddParameter2('output',              C.siString,                  '', None,       None, None, None, C.siClassifUnknown, C.siPersistable)
    cp.AddParameter2('frame_range',         C.siString, 'Complete Sequence', None,       None, None, None, C.siClassifUnknown, C.siPersistable)
    cp.AddParameter2('start_frame',         C.siInt4,                     0,    0, 2147483647,    0,  100, C.siClassifUnknown, C.siPersistable)
    cp.AddParameter2('end_frame',           C.siInt4,                     0,    0, 2147483647,    0,  100, C.siClassifUnknown, C.siPersistable)
    cp.AddParameter2('temporal_frames',     C.siInt4,                     0,    0,          2,    0,    2, C.siClassifUnknown, C.siPersistable)
    cp.AddParameter2('variance',            C.siFloat,                  0.5,    0,          1,    0,    1, C.siClassifUnknown, C.siPersistable)
    cp.AddParameter2('pixel_search_radius', C.siInt4,                     9,    6,         21,    6,   21, C.siClassifUnknown, C.siPersistable)
    cp.AddParameter2('pixel_patch_radius',  C.siInt4,                     3,    0,          6,    0,    6, C.siClassifUnknown, C.siPersistable)
    cp.AddParameter2('light_group_aovs',    C.siString,                  '', None,       None, None, None, C.siClassifUnknown, C.siPersistable)
    return true

# Tip: Use the "Refresh" option on the Property Page context menu to 
# reload your script changes and re-execute the DefineLayout callback.
def arnold_denoiser_DefineLayout( in_ctxt ):
    layout = in_ctxt.Source
    layout.Clear()

    file_types = 'OpenEXR files (*.exr)|*.exr||'

    item = layout.AddItem('input', 'Input', C.siControlFilePath)
    item.SetAttribute(C.siUIFileFilter, file_types)
    item.SetAttribute(C.siUIOpenFile, True)
    item.SetAttribute(C.siUIFileMustExist, True)
    item.SetAttribute(C.siUILabelMinPixels, 40)
    item.SetAttribute(C.siUILabelPercentage, 20)

    item = layout.AddItem('output', 'Output', C.siControlFilePath)
    item.SetAttribute(C.siUIFileFilter, file_types)
    item.SetAttribute(C.siUILabelMinPixels, 40)
    item.SetAttribute(C.siUILabelPercentage, 20)

    frame_ranges = [
             'Single Frame',      'Single Frame',
              'Start / End',       'Start / End',
        'Complete Sequence', 'Complete Sequence'
        ]
    item = layout.AddEnumControl('frame_range', frame_ranges, 'Frame Range')
    item.SetAttribute(C.siUILabelMinPixels, 80)

    layout.AddRow()
    layout.AddItem('start_frame', 'Start Frame')
    layout.AddItem('end_frame', 'End Frame')
    layout.EndRow()

    item = layout.AddItem('temporal_frames', 'Temporal Stability Frames')
    item.SetAttribute(C.siUILabelMinPixels, 140)

    item = layout.AddItem('variance', 'Variance')
    item.SetAttribute(C.siUILabelMinPixels, 140)

    item = layout.AddItem('pixel_search_radius', 'Pixel Search Radius')
    item.SetAttribute(C.siUILabelMinPixels, 140)

    item = layout.AddItem('pixel_patch_radius', 'Pixel Patch Radius')
    item.SetAttribute(C.siUILabelMinPixels, 140)

    item = layout.AddItem('light_group_aovs', 'Light Group AOVs')
    item.SetAttribute(C.siUILabelMinPixels, 100)

    item = layout.AddButton('denoise', 'Denoise')
    item.SetAttribute(C.siUICX, 80)
    item.SetAttribute(C.siUICY, 30)
    return true

def arnold_denoiser_OnInit( ):
    Application.LogMessage('arnold_denoiser_OnInit called', C.siVerbose)
    frame_range_logic()

def arnold_denoiser_OnClosed( ):
    Application.LogMessage('arnold_denoiser_OnClosed called', C.siVerbose)

def arnold_denoiser_input_OnChanged( ):
    Application.LogMessage('arnold_denoiser_input_OnChanged called', C.siVerbose)
    oParam = PPG.input
    paramVal = oParam.Value
    Application.LogMessage(str('New value: ') + str(paramVal), C.siVerbose)
    input_logic()

def arnold_denoiser_frame_range_OnChanged( ):
    Application.LogMessage('arnold_denoiser_frame_range_OnChanged called', C.siVerbose)
    oParam = PPG.frame_range
    paramVal = oParam.Value
    Application.LogMessage(str('New value: ') + str(paramVal), C.siVerbose)
    frame_range_logic()

def arnold_denoiser_denoise_OnClicked( ):
    Application.LogMessage('arnold_denoiser_denoise_OnClicked called', C.siVerbose)
    cp = PPG.Inspected(0)
    doDenoise(cp)

def frame_range_logic():
    if PPG.frame_range.Value == 'Start / End':
        PPG.start_frame.Enable(True)
        PPG.end_frame.Enable(True)
    elif PPG.frame_range.Value == 'Single Frame':
        PPG.start_frame.Enable(True)
        PPG.end_frame.Enable(False)
    else:
        PPG.start_frame.Enable(False)
        PPG.end_frame.Enable(False)

def input_logic():
    # convert softimage file sequnce syntax
    inputFile = PPG.input.Value
    inputSeq = ImageSequence(inputFile)
    start_frame = inputSeq.start
    end_frame = inputSeq.end

    outputSeq = ImageSequence(inputFile)
    outputSeq.addFilebaseSuffix('_denoised')

    PPG.start_frame.Value = start_frame
    PPG.end_frame.Value = end_frame
    PPG.output.Value = outputSeq.squares()


class ImageSequence(object):
    si_re = re.compile(r'(.*)\[(\d+)\.{2}(\d+);(\d+)\](.*)(\..+)')
    square_re = re.compile(r'(.*?)(#+)(.*)(\..+)')
    def __init__(self, path=None):
        # Class that make conversions.

        self.start = 0
        self.end = 0
        self.padding = 4
        self.filebase = u''
        self.filehead = u''
        self.ext = u''
        self._creation_path = None
        
        if path is not None:
            self._creation_path = path
            
            if self.si_re.match(path):
                self.parseSiSequence()
            elif self.square_re.match(path):
                self.parseSquareSequence()
            else:
                self.parseDigitSequence()
            
    def __repr__(self):
        return 'ImageSequence(start={}, end={}, padding={}, filebase={}, filehead={}, ext={})'.format(
            self.start,
            self.end,
            self.padding,
            self.filebase,
            self.filehead,
            self.ext
            )
        
    def parseSiSequence(self):
        re_result = self.si_re.search(self._creation_path)
        
        self.start = int(re_result.group(2))
        self.end = int(re_result.group(3))
        self.padding = int(re_result.group(4))
        self.filebase = re_result.group(1)
        self.filehead = re_result.group(5)
        self.ext = re_result.group(6)
    
    
    def parseSquareSequence(self):
        re_result = self.square_re.search(self._creation_path)
        
        self.padding = len(re_result.group(2))
        self.filebase = re_result.group(1)
        self.filehead = re_result.group(3)
        self.ext = re_result.group(4)
        
        begin_pos = len(self.filebase)
        end_pos = begin_pos + self.padding
        
        end_frame = start_frame = 0
        globFile = self.filebase + u'[0-9]' * self.padding + self.filehead + self.ext
        filesList = glob.glob(globFile) or []
        
        for matchingFile in filesList:
            frame_token = int(matchingFile[begin_pos:end_pos])
            if start_frame < 0 or frame_token < start_frame:
                start_frame = frame_token
            if frame_token > end_frame:
                end_frame = frame_token
        
        self.start = start_frame
        self.end = end_frame


    def parseDigitSequence(self):
        base, ext = os.path.splitext(self._creation_path)
        
        head_length = 0
        padding = 0
        for c in reversed(base):
            if u'0' <= c < u'9':
                padding += 1
            elif padding > 0:
                break # I already found numerical characters and they're finished now
            else:
                # still haven't found a numerical parameter
                head_length += 1
        
        if padding > 0:
            if head_length > 0:
                self.start = int(base[-(head_length+padding):-head_length])
                self.filehead = base[-head_length:]
            else:
                self.start = int(base[-(head_length+padding):])
                self.filehead = u''
            self.end = self.start
            self.padding = padding
            self.filebase = base[:-(head_length+padding)]
            self.ext = ext
    
    
    def si(self):
        if self.start == self.end:
            # if start = end, return the single frame
            return self.frame(self.start)
        return u'{}[{}..{};{}]{}{}'.format(self.filebase, self.start, self.end, self.padding, self.filehead, self.ext)
        
    def squares(self):
        if self.start == self.end:
            # if start = end, return the single frame
            return self.frame(self.start)
        return (u'{}' + u'#' * self.padding + '{}{}').format(self.filebase, self.filehead, self.ext)
        
    def frame(self, frame):
        return (u'{}{:0' + str(self.padding) + u'd}{}{}').format(self.filebase, frame, self.filehead, self.ext)
            
            
    def addFilebaseSuffix(self, suffix):
        if self.filebase[-1] in u'._':
            new_filebase = self.filebase[:-1]
            new_filebase += suffix
            new_filebase += self.filebase[-1:]
        else:
            new_filebase = self.filebase + suffix
            
        self.filebase = new_filebase


def doDenoise(cp):
    #if self.running:
    #    return

    inFile = cp.input.Value
    outFile = cp.output.Value

    if inFile == '':
        XSIUIToolkit.MsgBox('An input file must be selected', C.siMsgOkOnly, 'Arnold Denoiser')
        return False
    if outFile == '':
        XSIUIToolkit.MsgBox('An output file must be selected', C.siMsgOkOnly, 'Arnold Denoiser')
        return False

    inFile = ImageSequence(inFile)
    outFile = ImageSequence(outFile)

    #self.running = True
    start_frame = cp.start_frame.Value
    frame_range = cp.frame_range.Value
    if frame_range == u'Single Frame':
        end_frame = start_frame
    elif frame_range == u'Start / End':
        end_frame = cp.end_frame.Value
    else: # complete sequence, need to check on disk all the existing input files
        start_frame, end_frame = inFile.start, inFile.end
        

    temporal_frames = cp.temporal_frames.Value
    pixel_search_radius = cp.pixel_search_radius.Value
    pixel_patch_radius = cp.pixel_patch_radius.Value
    variance = cp.variance.Value
    light_group_aovs = cp.light_group_aovs.Value

    runDenoise(start_frame, end_frame, inFile, outFile, temporal_frames, pixel_search_radius, pixel_patch_radius, variance, light_group_aovs)

    return True


def runDenoise(start_frame, end_frame, inFile, outFile, temporal_frames, pixel_search_radius, pixel_patch_radius, variance, light_group_aovs):
    pb = XSIUIToolkit.ProgressBar
    pb.Caption = 'Denoising ...'
    pb.Maximum = int(end_frame) - int(start_frame) + 1
    pb.Visible = True
    pb.StatusText = '{}/{}'.format(0, pb.Maximum)
    
    run = True
    f = start_frame
    while run and f <= end_frame:
        Application.LogMessage('[sitoa] Denoising image {} '.format(inFile.frame(f)))
        t = threading.Thread(target=denoiseImage, args=(inFile, outFile, f, temporal_frames, pixel_search_radius, pixel_patch_radius, variance, light_group_aovs))
        t.start()

        while t.is_alive():
            if pb.CancelPressed:
                run = False
                Application.LogMessage('[sitoa] Stopping Arnold Denoiser after the current frame is done...')
            Application.Desktop.RedrawUI()
            sleep(0.01)  # just to limit the RedrawUI a bit.
        else:
            if not run:
                Application.LogMessage('[sitoa] Arnold Denoiser has stopped.')

        i = pb.Increment()
        pb.StatusText = '{}/{}'.format(i, pb.Maximum)
        f += 1

    else:
        if run:
            Application.LogMessage('[sitoa] Arnold Denoiser has finished.')


def denoiseImage(inFile, outFile, f, temporal_frames, pixel_search_radius, pixel_patch_radius, variance, light_group_aovs):
    inFile = inFile.frame(f)
    outFile = outFile.frame(f)
    
    noice_binary = os.path.join(os.path.dirname(Application.Plugins('Arnold Render').Filename), 'noice')
    if sys.platform == 'win32':
        noice_binary += '.exe'
    
    cmd = [noice_binary]
    cmd += ['-i', inFile, '-o', outFile]
    cmd += ['-ef', str(temporal_frames), '-sr', str(pixel_search_radius), '-pr', str(pixel_patch_radius), '-v', str(variance)]

    if len(light_group_aovs) > 0:
        light_group_split = light_group_aovs.split(' ')
        for light_group in light_group_split:
            cmd += ['-l', light_group]

    Application.LogMessage('Starting Arnold Denoiser with command: ' + subprocess.list2cmdline(cmd), C.siVerbose)
    res = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=_no_window).communicate()[0]
    Application.LogMessage(res, C.siVerbose)
