from functools import partial
import Live
import logging
from typing import Optional, Tuple, Any
from .handler import AbletonOSCHandler


class CustomHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "custom"

    def init_api(self):

        logger = logging.getLogger("abletonosc")

        def device_nav_first():
            NavDirection = Live.Application.Application.View.NavDirection
            devices = self.song.view.selected_track.devices

            while selected_device() != devices[0]:
                _scroll_selected_device_chain(NavDirection.left)

            ## for when it is selected but out of focus
            _scroll_selected_device_chain(NavDirection.left)

        def device_nav_last():
            NavDirection = Live.Application.Application.View.NavDirection
            devices = self.song.view.selected_track.devices

            while selected_device() != devices[-1]:
                _scroll_selected_device_chain(NavDirection.right)

                if selected_device().name == "CK Utility":
                    return

        def scroll_to_device(params):
            NavDirection = Live.Application.Application.View.NavDirection

            target_index = params[0]

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

        def replace_spaces(st):
            return st.replace(" ", "_")

        def selected_device_name(params):
            device = selected_device()
            logger.info(f"selected_device_name dev = {device}")
            logger.info(f"selected_device_name dev = {device.name}")
            logger.info(f"selected_device_name dev = {replace_spaces(device.name)}")
            return (replace_spaces(device.name),)

        def selected_device_type(params):
            return (replace_spaces(selected_device().class_display_name),)

        def selected_device_ob(params):
            d = selected_device()
            return (d.name, d.class_display_name, d.type,)

        def selected_device():
            return self.song.view.selected_track.view.selected_device

        def track_color_to_red(params):
            current_index = self.song.view.selected_track.color_index
            self.song.view.selected_track.color_index = params[0]
            return (current_index,)


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
            # self.log_message(f"show_message")
            # self.manager.show_message(f"TEST")
            self.manager.show_message(f"{params[0]}")
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
            val = params[0]
            for d in self.song.master_track.devices:
                if d.name == "Bass Only":
                    # d.parameters[0].value = (d.parameters[0].value + 1) % 2
                    d.parameters[0].value = int(val)

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

        def track_nav_inc(param):
            all_tracks = len(self.song.tracks)
            selected_track = self.song.view.selected_track  # Get the currently selected track

            logger.info(f"Selected track name is {selected_track.name}")

            if selected_track.name == "Master":
                self.manager.show_message("Can't increment from Master")

            next_index = list(self.song.tracks).index(selected_track) + 1  # Get the index of the selected track

            if next_index < all_tracks:
                self.song.view.selected_track = self.song.tracks[next_index]

        def track_nav_dec(param):
            selected_track = self.song.view.selected_track  # Get the currently selected track

            if selected_track.name == "Master":
                next_index = len(list(self.song.tracks)) - 1
            else:
                next_index = list(self.song.tracks).index(selected_track) - 1  # Get the index of the selected track

            if next_index >= 0:
                self.song.view.selected_track = self.song.tracks[next_index]

        def _scroll_device_chain(direction):
            view = self.application.view
            if not view.is_view_visible('Detail') or not view.is_view_visible('Detail/DeviceChain'):
                view.show_view('Detail')
                view.show_view('Detail/DeviceChain')
            else:
                view.scroll_view(direction, 'Detail/DeviceChain', False)

        def fire_scene(params):
            logger.info(f"fire_scene, params {params}")
            self.song.scenes[params[0]].fire()
            name_clips_to_scene_number_and_clip_length(params)

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
                        name = track.name.split(maxsplit=1)[1]


                        clip.name = f"{scene_number+1} {name} ({loop_length})"

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
        self.osc_server.add_handler("/live/view/message", show_message)
