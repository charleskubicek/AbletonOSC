import dataclasses
from functools import partial
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.ControlSurface import ControlSurface
import Live
import logging
from typing import Optional, Tuple, Any

from .handler import AbletonOSCHandler
import time
import re
from functools import partial
from ..pythonosc.udp_client import SimpleUDPClient
from ..pythonosc.osc_message_builder import ArgValue

class ClipOps(AbletonOSCHandler):

    def __init__(self, manager):
        super().__init__(manager)
        self._manager = manager

        ## TODO implement tripples as well as bars
        self._note_shift_quantization = 0.25

    def create_clip_and_notes(self, notes, title, length=4):
        '''
        Create a clip with the given notes and title.

        If its in the arrange view, add the notes to the selected clip.

        :param notes:
        :param title:
        :return:
        '''

        clip = self.get_or_create_selected_clip(length)
        if clip is not None:
            clip.loop_end = length  # a clip from arrangement might be different
            clip.remove_notes_extended(from_time=0, from_pitch=0, time_span=clip.loop_end, pitch_span=128)

            clip.add_new_notes(tuple(notes))
            clip.name = title


    def get_or_create_selected_clip(self, length, create=True, remove_existing=True):
        vw = self.application.view.focused_document_view
        # self.log("focused_document_view: " + str(vw))

        if vw == 'Arranger':

            tm = self.song.current_song_time
            # self.log_message("current_song_time: " + str(tm))

            track = self.song.view.selected_track
            for clip in track.arrangement_clips:
                # self.log(f"is audio clip {clip.is_audio_clip})")
                # self.log(f"is audio clip {clip.is_midi_clip})")
                # self.log(f"start time {clip.start_time})")
                # self.log(f"start marker {clip.start_marker})")
                #
                # self.log(f"end time {clip.end_time})")
                # self.log(f"end marker {clip.loop_end})")
                # self.log(f"end time {str(clip)}")
                # self.log(f"loop end {clip.loop_end})")
                # self.log(f"end time {str(clip)}")

                if clip.is_midi_clip and clip.start_time <= tm < clip.end_time:
                    return clip

            # self.create_clip_and_copy_it_to_arrangement(track, Patterns.c_line, tm)


        elif not self.song.view.highlighted_clip_slot.has_clip and create:
            self.song.view.highlighted_clip_slot.create_clip(float(length))
            clip = self.song.view.highlighted_clip_slot.clip

            return clip
        elif self.song.view.highlighted_clip_slot.has_clip:
            clip = self.song.view.highlighted_clip_slot.clip

            if remove_existing:
                clip.remove_notes_extended(from_time=0, from_pitch=0, time_span=clip.loop_end, pitch_span=128)

            return clip

        return None

    def shift_clip_notes_right(self):
        clip = self.get_or_create_selected_clip(-1, create=False, remove_existing=False)
        if clip is not None:
            notes = clip.get_all_notes_extended()
            for note in notes:
                note.start_time = note.start_time + self._note_shift_quantization

            clip.apply_note_modifications(notes)


    def shift_clip_notes_left(self):
        clip = self.get_or_create_selected_clip(-1, create=False, remove_existing=False)
        if clip is not None:
            notes = clip.get_all_notes_extended()
            for note in notes:
                note.start_time = note.start_time - self._note_shift_quantization

            clip.apply_note_modifications(notes)


class PatternCycler(AbletonOSCHandler):
    def __init__(self, ins, patterns, clip_ops):
        super().__init__(ins)
        self._control_surface = ins
        self._patterns = patterns
        self._clip_ops = clip_ops

        self.counter = 0
        self.last_press = int(time.time())

    def was_used_within_window(self):
        return int(time.time()) - self.last_press < 4

    def next(self):
        if not self.was_used_within_window():
            self.counter = 0

        name, notes = self._patterns[self.counter]
        self._clip_ops.create_clip_and_notes(notes, name)
        self.counter = (self.counter + 1) % len(self._patterns)

        self.last_press = time.time()


class Patterns(object):
    c_line = [Live.Clip.MidiNoteSpecification(pitch=60, start_time=0, duration=4, velocity=127)]
    g_line = [Live.Clip.MidiNoteSpecification(pitch=55, start_time=0, duration=4, velocity=127)]
    notes_c_kicks = [
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=0, duration=1, velocity=127),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=1, duration=1, velocity=127),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=2, duration=1, velocity=127),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=3, duration=1, velocity=127)
    ]

    notes_off_beat = [
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=0.5, duration=0.5, velocity=127),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=1.5, duration=0.5, velocity=127),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=2.5, duration=0.5, velocity=127),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=3.5, duration=0.5, velocity=127)
    ]

    # midi_drum_loops = [
    #     (build_loop([[0,0,9,0],[0,0,9,3],[0,0,0,0],[0,9,3,0]]))
    # ]

    notes_c_16s = [
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=0, duration=0.25, velocity=75),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=0.25, duration=0.25, velocity=100),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=0.5, duration=0.25, velocity=127),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=0.75, duration=0.25, velocity=100),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=1, duration=0.25, velocity=75),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=1.25, duration=0.25, velocity=100),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=1.5, duration=0.25, velocity=127),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=1.75, duration=0.25, velocity=100),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=2, duration=0.25, velocity=75),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=2.25, duration=0.25, velocity=100),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=2.5, duration=0.25, velocity=127),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=2.75, duration=0.25, velocity=100),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=3, duration=0.25, velocity=75),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=3.25, duration=0.25, velocity=100),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=3.5, duration=0.25, velocity=127),
        Live.Clip.MidiNoteSpecification(pitch=60, start_time=3.75, duration=0.25, velocity=100)
    ]

    basic_midi_cycles = [
        ('C Line', c_line),
        ('C Beats', notes_c_kicks),
        ('C Offbeat', notes_off_beat),
        ('C 16s', notes_c_16s),
        ('G Line', g_line),
    ]


class TouchOSCClient:

    def __init__(self, host='127.0.0.1', port=5005):
        self.client = SimpleUDPClient(host, port)
        self.logger = logging.getLogger("touchosc")

        self.logger.info(f"TouchOSCClient created with host {host} and port {port}")

    def send_message(self, address: str, value: ArgValue) -> None:
        # self.logger.info(f"Sending message {address} {value}")
        self.client.send_message(address, value)

class TouchOSCMultiClient:

    def __init__(self, clients: list[TouchOSCClient]):
        self.clients = clients

    def send_message(self, address: str, value: ArgValue) -> None:
        for client in self.clients:
            client.send_message(address, value)

class CustomHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.logger = logging.getLogger("abletonosc")
        self.class_identifier = "custom"
        self.clip_ops = ClipOps(self)
        self.midi_pattern_cycler = PatternCycler(self, Patterns.basic_midi_cycles, self.clip_ops)

        self.name_guesser = NameGuesser(self, self.song)
        self.touch_osc = TouchOSCMultiClient([
            # TouchOSCClient(host='127.0.0.1'),
            # TouchOSCClient(host='192.168.68.84', port=5015)
        ])

        self.the_selected_device = None

    def log_message(self, message):
        self.logger.info(message)

    def parameter_0_listener(self):
        self.parameter_listener(0)
    def parameter_1_listener(self):
        self.parameter_listener(1)
    def parameter_2_listener(self):
        self.parameter_listener(2)
    def parameter_3_listener(self):
        self.parameter_listener(3)
    def parameter_4_listener(self):
        self.parameter_listener(4)
    def parameter_5_listener(self):
        self.parameter_listener(5)
    def parameter_6_listener(self):
        self.parameter_listener(6)
    def parameter_7_listener(self):
        self.parameter_listener(7)
    def parameter_8_listener(self):
        self.parameter_listener(8)
    def parameter_9_listener(self):
        self.parameter_listener(9)
    def parameter_10_listener(self):
        self.parameter_listener(10)
    def parameter_11_listener(self):
        self.parameter_listener(11)
    def parameter_12_listener(self):
        self.parameter_listener(12)
    def parameter_13_listener(self):
        self.parameter_listener(13)
    def parameter_14_listener(self):
        self.parameter_listener(14)
    def parameter_15_listener(self):
        self.parameter_listener(15)
    def parameter_16_listener(self):
        self.parameter_listener(16)


    def parameter_listener(self, parameter_number):
        self.logger.info(f"parameter_1_listener; selected device is {self.the_selected_device.name}")
        param = self.the_selected_device.parameters[parameter_number]
        self.touch_osc.send_message(f"/selected-device/parameter-update", [parameter_number, str(param.value), param.name, param.min, param.max])

    def on_device_changed(self, new_device):
        self.logger.info("selected_device_changed: " + str(new_device))
        if new_device is None:
            return

        device = new_device
        # device_name = selected_device_name(None)[0]
        self.logger.info(f"selected_device_changed {new_device.name}")
        self.touch_osc.send_message("/selected-device/name", new_device.name)


        if self.the_selected_device is not None:
            for i, param in enumerate(device.parameters):
                if i < 17 and i > 0:
                    listener = getattr(self, f"parameter_{i}_listener")
                    self.logger.info(f"removing listener from {param.name}; is on: {param.value_has_listener(listener)}")
                    if param.value_has_listener(listener):
                        param.remove_value_listener(listener)

        self.the_selected_device = device

        for i, param in enumerate(device.parameters):
            if i < 17 and i > 0:
                listener = getattr(self, f"parameter_{i}_listener")
                self.touch_osc.send_message(f"/selected-device/parameter-update", [i, str(param.value), param.name, param.min, param.max])
                param.add_value_listener(listener)

        self.touch_osc.send_message("/selected-device/parameter-update-complete", len(device.parameters))


    def init_api(self):

        logger = logging.getLogger("abletonosc")

        def selected_device_changed():

            self.on_device_changed(selected_device())

        # def selected_device_changed():
        #     self.logger.info("selected_device_changed")
        #     device_name = selected_device_name(None)[0]
        #     self.logger.info(f"selected_device_changed {device_name}")
        #     self.touch_osc.send_message("/selected-device/name", device_name)
        #
        #     device = selected_device()
        #
        #     if self.the_selected_device is not None:
        #         for i, param in enumerate(device.parameters):
        #             if i == 1:
        #                 if self.the_selected_device.parameters[1].value_has_listener(self.parameter_1_listener):
        #                     self.the_selected_device.parameters[1].remove_value_listener(self.parameter_1_listener)
        #
        #     self.the_selected_device = device
        #
        #     for i, param in enumerate(device.parameters):
        #         if i < 17:
        #             self.touch_osc.send_message(f"/selected-device/parameter-update", [i, str(param.value), param.name, param.min, param.max])
        #
        #         if i == 1:
        #             param.add_value_listener(partial(self.parameter_1_listener))
        #
        #     self.touch_osc.send_message("/selected-device/parameter-update-complete", len(device.parameters))


        def device_nav_first():
            NavDirection = Live.Application.Application.View.NavDirection
            devices = self.song.view.selected_track.devices

            while selected_device() != devices[0]:
                _scroll_selected_device_chain(NavDirection.left)

            ## for when it is selected but out of focus
            _scroll_selected_device_chain(NavDirection.left)
            selected_device_changed()

        def device_nav_last():
            NavDirection = Live.Application.Application.View.NavDirection
            devices = self.song.view.selected_track.devices

            while selected_device() != devices[-1]:
                _scroll_selected_device_chain(NavDirection.right)

                if selected_device().name == "CK Utility":
                    selected_device_changed()
                    return

        def scroll_to_device(params):
            NavDirection = Live.Application.Application.View.NavDirection

            target_index = int(params[0])

            selected = self.selected_device()
            devices = self.song.view.selected_track.devices

            current_index = self.tuple_index(devices, selected)

            loop_check = 0

            while target_index < current_index and loop_check < 100:
                _scroll_selected_device_chain(NavDirection.left)
                current_index = self.tuple_index(devices, selected)
                loop_check += 1

            while target_index > current_index and loop_check < 100:
                _scroll_selected_device_chain(NavDirection.right)
                current_index = self.tuple_index(devices, selected)
                loop_check += 1

        def _scroll_selected_device_chain(direction):
            view = self.application.view
            if not view.is_view_visible('Detail') or not view.is_view_visible('Detail/DeviceChain'):
                view.show_view('Detail')
                view.show_view('Detail/DeviceChain')
            else:
                view.scroll_view(direction, 'Detail/DeviceChain', False)

        def print_views():
            view = self.application.view
            logger.info(f"detail visible {view.is_view_visible('Detail')}")
            logger.info(f"detail/DeviceChain visible {view.is_view_visible('Detail/DeviceChain')}")
            logger.info(f"Arranger visible {view.is_view_visible('Arranger')}")
            logger.info(f"Session visible {view.is_view_visible('Session')}")

        def toggle_first_last_device(params):
            print_views()
            devices = self.song.view.selected_track.devices

            if len(devices) == 0:
                return

            if selected_device() != devices[0]:
                device_nav_first()
            else:
                device_nav_last()

                print_views()

        def toggle_instrument_utility(params):
            track = self.song.view.selected_track
            devices = self.song.view.selected_track.devices

            if not track.has_midi_input:
                toggle_first_last_device(params)

            if len(devices) == 0:
                return

            if str(selected_device().type) == "instrument":
                device_nav_last()
            else:
                navigate_to_instrument(params)

        def device_nav_left_ignoring_inner_devices(params):
            NavDirection = Live.Application.Application.View.NavDirection

            selected = selected_device()
            devices = self.song.view.selected_track.devices

            if selected == devices[0]:
                return

            start = tuple_index(devices, selected)
            next = devices[start - 1]

            check = 0
            while selected_device() != next and check < 100:
                _scroll_selected_device_chain(NavDirection.left)
                check += 1

            selected_device_changed()


        def device_nav_right_ignoring_inner_devices(params):
            NavDirection = Live.Application.Application.View.NavDirection

            selected = selected_device()
            devices = self.song.view.selected_track.devices

            if selected == devices[-1]:
                return

            start = tuple_index(devices, selected)
            next = devices[start + 1]

            check = 0
            while selected_device() != next and check < 100:
                _scroll_selected_device_chain(NavDirection.right)
                check += 1

            selected_device_changed()

        def replace_spaces(st):
            return st.replace(" ", "_")

        def selected_device_name(params):
            device = selected_device()
            logger.info(f"selected_device_name dev = {device}")
            logger.info(f"selected_device_name dev = {device.name}")
            logger.info(f"selected_device_name dev = {replace_spaces(device.name)}")
            return (replace_spaces(device.name),)

        def device_info(params):
            device = selected_device()
            if device is None:
                return None
            else:
                logger.info(f"Values for {device.name} of type {device.class_name}")
                for i, p in enumerate((device).parameters):
                    logger.info(f" - [{i}] {p.name}:{p.value} ({p.min} -> {p.max} )")

                return None

        def selected_device_type(params):
            return (replace_spaces(selected_device().class_display_name),)

        def selected_device_ob(params):
            d = selected_device()
            if d is None:
                return None
            else:
                return (d.name, d.class_display_name, d.type,)

        def selected_device():
            return self.song.view.selected_track.view.selected_device

        @dataclasses.dataclass
        class OnOff:
            name: str

            def action(self, p):
                p.value = 0.0
                p.value = 1.0

            def __str__(self):
                return f"OnOff({self.name})"


        @dataclasses.dataclass
        class Inc:
            name: str

            def action(self, p):
                p.value = p.value + 1.0

            def __str__(self):
                return f"Inc({self.name})"

        @dataclasses.dataclass
        class Dec:
            name: str

            def action(self, p):
                p.value = p.value - 1.0

            def __str__(self):
                return f"Dec({self.name})"

        parameter_toggle_mappings = {
            "SQ Sequencer" : [OnOff("RandPitch"),
                              OnOff("RandOct"),
                              OnOff("VelRandom"),
                              OnOff("RandLength"),
                              OnOff("ResetVelocity"),
                              OnOff("ResetLength"),
                              Dec("SQMax"),
                              Inc("SQMax"),
                              OnOff("ShiftLeft"),
                              OnOff("ShiftRight"),
                              ]
        }


        def selected_device_parameter_toggle(params):
            device = selected_device()

            if device is None or device.name not in parameter_toggle_mappings:
                return ()

            parameter_mapping_index = int(params[0])
            # logger.info(f"selected_device_parameter_toggle dev = {parameter_mapping_index}")
            parameter_op = parameter_toggle_mappings[device.name][parameter_mapping_index]
            logger.info(f"selected_device_parameter_toggle device {device.name}:{parameter_op} from index {parameter_mapping_index}]")

            show_message(f"Parameter {parameter_op}")

            for p in device.parameters:
                # logger.info(f"selected_device_parameter_toggle checking param {p.name} against {parameter_op} ({p.name == parameter_op})")
                if p.name == parameter_op.name:
                    parameter_op.action(p)

            return None

        def track_color_to_red(params):
            current_index = self.song.view.selected_track.color_index
            self.song.view.selected_track.color_index = int(params[0])
            return (current_index,)


        def press_rack_random_button(self):
            device = self.selected_device()

            if device is not None and device.can_have_chains:
                device.randomize_macros()

        def is_selected_device_an_instrument():
            return str(selected_device().type) == "instrument"

        def navigate_to_instrument(params):
            track = self.song.view.selected_track

            if not track.has_midi_input:
                return

            selected = selected_device()
            devices = track.devices

            target = find_instrument(track)

            if target is None:
                return

            selected_idx = tuple_index(devices, selected)
            target_idx = tuple_index(devices, target)

            logger.info(f"Found device {target.name} sct:{selected_idx}, tgt:{target_idx}")

            if selected_idx == target_idx:
                device_nav_right_ignoring_inner_devices(None)
                selected_idx = tuple_index(devices, selected_device())
                target_idx = tuple_index(devices, target)

            count_check = 0

            while selected_idx < target_idx and count_check < 50:
                device_nav_right_ignoring_inner_devices(None)
                selected = selected_device()
                selected_idx = tuple_index(devices, selected)
                count_check += 1

            while selected_idx > target_idx and count_check < 50:
                device_nav_left_ignoring_inner_devices(None)
                selected = selected_device()
                selected_idx = tuple_index(devices, selected)
                count_check += 1

        def find_instrument(track):
            for device in track.devices:
                logger.info(
                    f"type of {device.class_name} is {device.type} ({type(device.type)}, is inst: {device.type == 'instrument'})")
                if str(device.type) == "instrument":
                    return device

            return None

        def track_selected(params):
            selected = self.song.view.selected_track

            if selected is None:
                return

        def show_message(params):
            if type(params) is str:
                message = params
            else:
                message = str(params[0])
            # self.log_message(f"show_message")
            # self.manager.show_message(f"TEST")
            self.manager.show_message(message)
            # self.manager.show_message(f"TEST")
            return (1, 1)

        def is_in_arrangement(params):
            vw = self.application.view.focused_document_view

            return tuple([vw == 'Arranger'])

        def master_device_DT990_PRO_status(params):
            for d in self.song.master_track.devices:
                if 'DT990 PRO' in d.name:
                    return d.parameters[0].value,

            return None
        def master_device_DT990_PRO_turn_on(params):
            for d in self.song.master_track.devices:
                if 'DT990 PRO' in d.name:
                    d.parameters[0].value = 1
                    return d.parameters[0].value,

            return None
        def master_device_DT990_PRO_turn_off(params):
            for d in self.song.master_track.devices:
                if 'DT990 PRO' in d.name:
                    d.parameters[0].value = 0
                    return d.parameters[0].value,

            return None
        def master_device_ADAM_status(params):
            for d in self.song.master_track.devices:
                if 'ADAM' in d.name:
                    return d.parameters[0].value,

            return None
        def master_device_ADAM_turn_on(params):
            for d in self.song.master_track.devices:
                if 'ADAM' in d.name:
                    d.parameters[0].value = 1
                    return d.parameters[0].value,

            return None
        def master_device_ADAM_turn_off(params):
            for d in self.song.master_track.devices:
                if 'ADAM' in d.name:
                    d.parameters[0].value = 0
                    return d.parameters[0].value,

            return None

        def master_device_ref_track_status(params):
            for t in self.song.tracks:
                if t.name.endswith('Ref') or t.name.endswith('Ref'):
                    if t.solo:
                        return 1.0,

            return 0.0,

        def master_device_ref_track_on(params):
            found = False
            for t in self.song.tracks:
                if t.name.endswith('Ref') or t.name.endswith('Ref'):
                    found = True
                    break

            if not found:
                return 0.0,

            for t in self.song.tracks:
                if t.name.endswith('Ref') or t.name.endswith('Ref'):
                    t.solo = True
                    t.mute = False
                else:
                    t.mute = True

            return 1.0,


        def master_device_ref_track_off(params):
            found = False
            for t in self.song.tracks:
                if t.name.endswith('Ref') or t.name.endswith('Ref'):
                    found = True
                    break

            if not found:
                return 0.0,

            for t in self.song.tracks:
                if t.name.endswith('Ref') or t.name.endswith('Ref'):
                    t.solo = False
                    t.mute = True
                else:
                    t.mute = False

            return 0.0,

        def toggle_ref_track(params):
            for t in self.song.tracks:
                if t.name.endswith('Ref') or t.name.endswith('Ref'):
                    if t.solo:
                        t.solo = False
                        t.mute = True
                    else:
                        t.solo = True
                        t.mute = False

        def toggle_mono_on_master(params):
            for d in self.song.master_track.devices:
                if d.name == "Mono":
                    d.parameters[0].value = (d.parameters[0].value + 1) % 2

                    self.manager.show_message(f"Mono set to {d.parameters[0].value}")


        def master_device_bass_only_status(params):
            for d in self.song.master_track.devices:
                if d.name == "Bass Only":
                    return d.parameters[0].value,

            return None


        def master_device_bass_only_on(params):
            return set_master_chanel_device_to("Bass Only", 1.0)

            return 0.0,
        def master_device_bass_only_off(params):
            return set_master_chanel_device_to("Bass Only", 0.0)


        def master_device_bass_cut_status(params):
            for d in self.song.master_track.devices:
                if d.name == "Bass Cut":
                    return d.parameters[0].value,

            return None


        def master_device_bass_cut_on(params):
            return set_master_chanel_device_to("Bass Cut", 1.0)

            return 0.0,
        def master_device_bass_cut_off(params):
            return set_master_chanel_device_to("Bass Cut", 0.0)


        def master_device_mono_status(params):
            for d in self.song.master_track.devices:
                if d.name == "Mono":
                    return d.parameters[0].value,

            return None
        def master_device_mono_on(params):
            return set_master_chanel_device_to("Mono", 1.0)

            return 0.0,
        def master_device_mono_off(params):
            return set_master_chanel_device_to("Mono", 0.0)

            return 0.0,
        def set_master_chanel_device_to(name, value):
            for d in self.song.master_track.devices:
                if d.name == name:
                    d.parameters[0].value = value
                    return d.parameters[0].value,

            return 0.0,


        def toggle_device_called_DT990_PRO_on_master(params):

            logger.info(f"toggle_device_called_DT990_PRO_on_master")

            for d in self.song.master_track.devices:
                if 'DT990 PRO' in d.name:
                    d.parameters[0].value = (d.parameters[0].value + 1) % 2
                    logger.info(f"toggle_device_called_DT990_PRO_on_master, new val {d.parameters[0].value}")
                    self.manager.show_message(f"Sonaworks DT 990 set to {d.parameters[0].value}")

        def toggle_mono_on_master(params):

            for d in self.song.master_track.devices:
                if d.name == "Mono":
                    d.parameters[0].value = (d.parameters[0].value + 1) % 2

                    self.manager.show_message(f"Mono set to {d.parameters[0].value}")

        def toggle_high_pass_on_master(params):

            for d in self.song.master_track.devices:
                if d.name == "No Bass":
                    d.parameters[0].value = (d.parameters[0].value + 1) % 2

                    self.manager.show_message(f"No Bass set to {d.parameters[0].value}")

        def toggle_low_pass_on_master(params):

            for d in self.song.master_track.devices:
                if d.name == "Bass Only":
                    d.parameters[0].value = (d.parameters[0].value + 1) % 2

                    self.manager.show_message(f"Bass Only set to {d.parameters[0].value}")

        def set_bass_only_master_device(params):
            val = int(params[0])
            for d in self.song.master_track.devices:
                if d.name == "Bass Only":
                    # d.parameters[0].value = (d.parameters[0].value + 1) % 2
                    d.parameters[0].value = val

                    self.manager.show_message(f"Bass Only set to {d.parameters[0].value}")

        def toggle_metric_ab_on_master(params):

            logger.info(f"toggle_device_called_Metric A/B_on_master")

            for d in self.song.master_track.devices:
                if 'Metric AB' in d.name:
                    logger.info(f"toggle_metric_ab_on_master d.parameters[1].value = {d.parameters[1].value}")
                    if d.parameters[1].value == 0:
                        d.parameters[1].value = 127
                    else:
                        d.parameters[1].value = 0

                    logger.info(f"toggle metirc ab, new val {d.parameters[1].value}")
                    self.manager.show_message(f"Metric AB set to {d.parameters[1].value}")

        def tuple_index(tuple, obj):
            for i in range(0, len(tuple)):
                logger.info(f"   tuple index, {tuple[i]} == {obj}")
                if tuple[i] == obj:
                    return i
            return False

        def move_selected_track_to_track_with_prefix(params):
            prefix = str(params[0])
            logger.info(f"move_selected_track_to_track_with_prefix, prefix: {prefix}")

            found = False

            for i, track in enumerate(self.song.tracks):
                logger.info("  checking track: " + track.name)
                if track.name.lower().startswith(prefix.lower()):
                    found = True
                    self.song.view.selected_track = track
                    break
                elif ' ' in track.name:
                    logger.info("  checking track after first space: " + track.name.split(' ')[1])
                    if track.name.split(' ')[1].lower() == prefix.lower():
                        found = True
                        self.song.view.selected_track = track
                        break

            if not found:
                logger.info("  no track found with prefix")

            selected_device_changed()

        def track_nav_inc(param):
            all_tracks = len(self.song.tracks)
            selected_track = self.song.view.selected_track  # Get the currently selected track

            logger.info(f"Selected track name is {selected_track.name}, tracks total: {all_tracks}, return tracks count: {len(self.song.return_tracks)}")
            next_index = 1

            is_return_track = selected_track in self.song.return_tracks
            is_main_track = selected_track == self.song.master_track
            logger.info(f"is return track: {is_return_track}")
            logger.info(f"is main track: {is_main_track}")

            if is_main_track and len(self.song.tracks) > 0:
                self.song.view.selected_track = self.song.tracks[0]
            elif not is_return_track:
                next_index = list(self.song.tracks).index(selected_track) + 1  # Get the index of the selected track
                logger.info(f"not_return, next_index: {next_index}, len: {len(self.song.return_tracks)}")

                if next_index < all_tracks:
                    self.song.view.selected_track = self.song.tracks[next_index]
                elif next_index == all_tracks and len(self.song.return_tracks) > 0:
                    self.song.view.selected_track = self.song.return_tracks[0]
            elif is_return_track:
                next_index = list(self.song.return_tracks).index(selected_track) + 1  # Get the index of the selected track
                logger.info(f"is_return, track name is: {selected_track.name}")
                logger.info(f"is_return, track index is: {list(self.song.return_tracks).index(selected_track)}")
                logger.info(f"is_return, next_index: {next_index}, len: {len(self.song.return_tracks)}")
                if next_index < len(self.song.return_tracks):
                    self.song.view.selected_track = self.song.return_tracks[next_index]
                elif next_index == len(self.song.return_tracks):
                    self.song.view.selected_track = self.song.master_track


            selected_device_changed()

        def track_nav_dec(param):
            all_tracks = len(self.song.tracks)
            selected_track = self.song.view.selected_track  # Get the currently selected track

            logger.info(f"Selected track name is {selected_track.name}, tracks total: {all_tracks}, return tracks count: {len(self.song.return_tracks)}")
            next_index = 1

            is_return_track = selected_track in self.song.return_tracks
            is_main_track = selected_track == self.song.master_track
            logger.info(f"is return track: {is_return_track}")
            logger.info(f"is main track: {is_main_track}")

            if is_main_track and len(self.song.tracks) > 0:
                if len(self.song.return_tracks) > 0:
                    self.song.view.selected_track = self.song.return_tracks[-1]
                else:
                    self.song.view.selected_track = self.song.tracks[-1]
            elif not is_return_track:
                next_index = list(self.song.tracks).index(selected_track) - 1  # Get the index of the selected track
                logger.info(f"not_return, next_index: {next_index}, len: {len(self.song.return_tracks)}")

                if next_index >= 0:
                    self.song.view.selected_track = self.song.tracks[next_index]
                elif next_index < 0:
                    self.song.view.selected_track = self.song.master_track
            elif is_return_track:
                next_index = list(self.song.return_tracks).index(selected_track) - 1  # Get the index of the selected track
                logger.info(f"is_return, track name is: {selected_track.name}")
                logger.info(f"is_return, track index is: {list(self.song.return_tracks).index(selected_track)}")
                logger.info(f"is_return, next_index: {next_index}, len: {len(self.song.return_tracks)}")
                if next_index >= 0:
                    self.song.view.selected_track = self.song.return_tracks[next_index]
                elif next_index < 0:
                    self.song.view.selected_track = self.song.tracks[-1]

            selected_device_changed()

        def _scroll_device_chain(direction):
            view = self.application.view
            if not view.is_view_visible('Detail') or not view.is_view_visible('Detail/DeviceChain'):
                view.show_view('Detail')
                view.show_view('Detail/DeviceChain')
            else:
                view.scroll_view(direction, 'Detail/DeviceChain', False)

        def fire_scene(params):
            logger.info(f"fire_scene, params {params}")
            logger.info(f"fire_scene, params {self.song.scenes}")
            self.song.scenes[int(params[0])].fire()
            name_clips_to_scene_number_and_clip_length(params)

        def iterate_perc_pattern(params):
            self.midi_pattern_cycler.next()

        def update_track_names(params):
            self.name_guesser.update_track_names()

        def name_clips_to_scene_number_and_clip_length(params):
            for track in self.song.tracks:  # for each track
                for clip_slot in track.clip_slots:  # for each clip slot
                    ## find the scene number of the clip slot
                    scene_number = next((i for i, scene in enumerate(self.song.scenes) if clip_slot in scene.clip_slots), None)

                    if clip_slot.has_clip:
                        clip = clip_slot.clip
                        # if not clip.name.startswith(f"{scene_number}."):

                        # get the loop start and end markers
                        loop_start = clip.loop_start
                        loop_end = clip.loop_end
                        loop_length = int(loop_end - loop_start)
                        # strip the first number and following space from teh track name
                        parts = track.name.split(maxsplit=1)

                        if len(parts) > 1:
                            name = parts[1]
                            clip.name = f"{scene_number+1} {name} ({loop_length})"

        def shift_clip_notes_right(params):
            self.clip_ops.shift_clip_notes_right()

        def shift_clip_notes_left(params):
            self.clip_ops.shift_clip_notes_left()

        self.osc_server.add_handler("/live/custom/fire/scene", fire_scene)
        self.osc_server.add_handler("/live/custom/set/toggle_inst_utility", toggle_instrument_utility)
        self.osc_server.add_handler("/live/custom/set/toggle_first_last", toggle_first_last_device)
        self.osc_server.add_handler("/live/custom/nav/to_instrument", navigate_to_instrument)
        self.osc_server.add_handler("/live/custom/scroll_to", scroll_to_device)
        self.osc_server.add_handler("/live/custom/get/is_arrangement_view", is_in_arrangement)
        self.osc_server.add_handler("/live/device/selected", selected_device_name)
        self.osc_server.add_handler("/live/device/selected_ob", selected_device_ob)
        self.osc_server.add_handler("/live/device/selected_type", selected_device_type)
        self.osc_server.add_handler("/live/set/selected_track/color_index", track_color_to_red)
        self.osc_server.add_handler("/live/view/nav/devices/prev", device_nav_left_ignoring_inner_devices)
        self.osc_server.add_handler("/live/view/nav/devices/next", device_nav_right_ignoring_inner_devices)
        self.osc_server.add_handler("/live/view/nav/tracks/inc", track_nav_inc)
        self.osc_server.add_handler("/live/view/nav/tracks/dec", track_nav_dec)
        self.osc_server.add_handler("/live/view/nav/tracks/by_prefix", move_selected_track_to_track_with_prefix)

        self.osc_server.add_handler("/live/device/selected/parameter_toggle", selected_device_parameter_toggle)

        self.osc_server.add_handler("/live/custom/toggle_dt990", toggle_device_called_DT990_PRO_on_master)
        self.osc_server.add_handler("/live/custom/master_dt990/status", master_device_DT990_PRO_status)
        self.osc_server.add_handler("/live/custom/master_dt990/on", master_device_DT990_PRO_turn_on)
        self.osc_server.add_handler("/live/custom/master_dt990/off", master_device_DT990_PRO_turn_off)

        self.osc_server.add_handler("/live/custom/master_adam/status", master_device_ADAM_status)
        self.osc_server.add_handler("/live/custom/master_adam/on", master_device_ADAM_turn_on)
        self.osc_server.add_handler("/live/custom/master_adam/off", master_device_ADAM_turn_off)

        self.osc_server.add_handler("/live/custom/toggle_ref_track", toggle_ref_track)
        self.osc_server.add_handler("/live/custom/master_ref_track/status", master_device_ref_track_status)
        self.osc_server.add_handler("/live/custom/master_ref_track/on", master_device_ref_track_on)
        self.osc_server.add_handler("/live/custom/master_ref_track/off", master_device_ref_track_off)

        self.osc_server.add_handler("/live/custom/master_mono/status", master_device_mono_status)
        self.osc_server.add_handler("/live/custom/master_mono/on", master_device_mono_on)
        self.osc_server.add_handler("/live/custom/master_mono/off", master_device_mono_off)

        self.osc_server.add_handler("/live/custom/master_bass_only/status", master_device_bass_only_status)
        self.osc_server.add_handler("/live/custom/master_bass_only/on", master_device_bass_only_on)
        self.osc_server.add_handler("/live/custom/master_bass_only/off", master_device_bass_only_off)

        self.osc_server.add_handler("/live/custom/master_bass_cut/status", master_device_bass_cut_status)
        self.osc_server.add_handler("/live/custom/master_bass_cut/on", master_device_bass_cut_on)
        self.osc_server.add_handler("/live/custom/master_bass_cut/off", master_device_bass_cut_off)

        self.osc_server.add_handler("/live/custom/toggle_metric_ab", toggle_metric_ab_on_master)
        # self.osc_server.add_handler("/live/custom/toggle_mono", toggle_mono_on_master)
        self.osc_server.add_handler("/live/custom/toggle_low_pass", toggle_low_pass_on_master)
        self.osc_server.add_handler("/live/custom/toggle_high_pass", toggle_high_pass_on_master)

        self.osc_server.add_handler("/live/custom/next_midi_pattern", iterate_perc_pattern)
        self.osc_server.add_handler("/live/custom/press_rack_random_button", press_rack_random_button)
        self.osc_server.add_handler("/live/custom/shift_clip_notes_right", shift_clip_notes_right)
        self.osc_server.add_handler("/live/custom/shift_clip_notes_left", shift_clip_notes_left)
        self.osc_server.add_handler("/live/custom/device_info", device_info)

        self.osc_server.add_handler("/live/view/message", show_message)


class NameGuesser(AbletonOSCHandler):

    def __init__(self, ins, song):
        super().__init__(ins)
        self._manager = ins
        self.logger = logging.getLogger("abletonosc")
        self._song = song
        self.default_track_colour_index = 69  # dark grey

    def log_message(self, message):
        self.logger.info(message)

    def get_name_of_instrument_or_sample(self, track):
        for d in track.devices:
            name, colour = self.get_name_of_instrument_or_sample_for_device(d)
            if name is not None:
                return name, colour

        return None, None

    def get_name_of_instrument_or_sample_for_device(self, d):
        found_name = None
        colour = None
        if str(d.type) == 'instrument':
            device_name = d.name
            class_name = d.class_name
            self.log_message("device class_name: " + str(d.class_name))
            self.log_message("device class_display_name: " + str(d.class_display_name))
            self.log_message(f"device name: {device_name}")

            if class_name == 'PluginDevice':
                found_name = device_name
                colour = 25
            if class_name == 'OriginalSimpler':
                found_name = device_name
                colour = 33
            elif device_name == 'Instrument Rack':
                name, c = self.find_rack_chain_names(d)
                if name is not None:
                    found_name = name
                    colour = c

            self.log_message(f"found_name: {found_name}")

            if found_name is not None:
                found_name = (found_name
                              .removeprefix("CK ")
                              .removeprefix("INST ")
                              .removeprefix("AYNIL "))

                return re.sub(r'[^a-zA-Z0-9]', '', found_name), colour

        return None, None

    def find_rack_chain_names(self, d):
        if d.can_have_chains:  # it's a rack #) == 'MidiEffectGroupDevice':
            self.log_message("d.chanins len: " + str(len(d.chains)))
            for chain in d.chains:
                for c_d in chain.devices:
                    name, colour = self.get_name_of_instrument_or_sample_for_device(c_d)
                    if name is not None:
                        return name, colour

        return None, None

    def update_track_names(self):

        not_updating = []

        for track in self._song.tracks:
            self.log_message(track.name)
            self.log_message(track.is_grouped)
            self.log_message(track.group_track)

        for track in self._song.tracks:
            try:
                self.log_message(f"------------------------------------------------")
                self.log_message(f"[{track.name}]")


                if self.is_track_grouping_other_tracks(track):
                    self.set_grouping_track_colour_from_others(track)

                if track.name.endswith('.') \
                        or self.is_track_grouping_other_tracks(track) \
                        or self.track_has_already_been_updated(track) \
                        or len(track.name) > 2:
                    self.log_message(f"[{track.name}] Skipping")
                    continue

                if track.name.startswith('[bip]'):
                    track.name = f"# {track.name[len('[bip] '):]} [bip]"
                    continue

                name_guess, colour = self.get_name_of_instrument_or_sample(track)
                self.log_message(f"[{track.name}] track name guess is {str(name_guess)}")

                track.name = name_guess
                track.color_index = colour

            except Exception as e:
                self.log_message(f"Exception: {str(e)}")
                not_updating.append(track.name)

    def is_track_grouping_other_tracks(self, the_track):
        for track in self.song.tracks:
            if track.group_track is not None and track.group_track.name == the_track.name:
                return True

        return False

    def set_grouping_track_colour_from_others(self, the_group_track):
        track_colors = [t.color_index for t in self.song.tracks if
                        t.group_track is not None and t.group_track.name == the_group_track.name]
        the_group_track.color_index = sorted(list(set(track_colors)))[0]

    def track_has_already_been_updated(self, the_track):
        return the_track.color_index != self.default_track_colour_index
