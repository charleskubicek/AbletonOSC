from functools import partial
import Live
from typing import Optional, Tuple, Any
from .handler import AbletonOSCHandler

class DeviceNavHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "device_nav"

    def init_api(self):

        def device_nav_first():
            NavDirection = Live.Application.Application.View.NavDirection
            devices = self.song.view.selected_track.devices

            for i in range(0, len(devices) + 14):
                _scroll_device_chain(NavDirection.left)

        def device_nav_last():
            NavDirection = Live.Application.Application.View.NavDirection
            devices = self.song.view.selected_track.devices

            for i in range(0, len(devices) + 14):
                _scroll_device_chain(NavDirection.right)

                if self.song.view.selected_track.view.selected_device == "CK Utility":
                    return

            _scroll_device_chain(NavDirection.left)


        def _scroll_device_chain(direction):
            view = self.application.view
            if not view.is_view_visible('Detail') or not view.is_view_visible('Detail/DeviceChain'):
                view.show_view('Detail')
                view.show_view('Detail/DeviceChain')
            else:
                view.scroll_view(direction, 'Detail/DeviceChain', False)

        def toggle_first_last_device(params):
            devices = self.song.view.selected_track.devices

            if len(devices) == 0:
                return

            if selected_device() != devices[0]:
                device_nav_first()
            else:
                device_nav_last()


        def selected_device():
            return self.song.view.selected_track.view.selected_device


        # self.osc_server.add_handler("/live/device_nav/set/toggle_first_last", toggle_first_last_device)
        # self.osc_server.add_handler("/live/custom/set/selected_track", set_selected_track)
