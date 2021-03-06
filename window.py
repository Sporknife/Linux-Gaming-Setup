import multi
import info
import widgets
import checker
import installer
import distro
import threading
import subprocess
import webbrowser
import os
from gi.repository import Gtk, Gio
import gi

gi.require_version("Gtk", "3.0")


class Handler:
    """
    This class is a handler class as the name says.
    The functions to be executed depending on a signal
    can be found by opening ui.glade with Glade
    """

    def __init__(self, Window_obj):
        self.window = Window_obj

    def refresh(self, *args):
        if self.window.refresh_btn.get_active():
            print("refreshed")

    def self_github_page(self, *args):
        print("Button clicked")
        webbrowser.open_new("https://github.com/RubixPower/Linux-Gaming-Setup")

    def lutris_page(self, *args):
        webbrowser.open_new("https://lutris.net/")

    def lutris_github(self, *args):
        webbrowser.open_new("https://github.com/lutris/lutris")

    def choose_release(self, button):
        selector = self.window.popout_programs.get(button.get_name())[2]
        selector.show_all()

    def toggl_nec_programs(self, button):
        name = button.get_name()
        active = button.get_active()
        if active and name in self.window.brother_programs:
            brother_program = self.window.brother_programs.get(name)
            button_obj = self.window.toggle_programs.get(brother_program)
            button_obj.set_active(True)

    def reset(self, *args):
        toggle_programs = self.window.toggle_programs
        for button_obj in toggle_programs.values():
            button_obj.set_active(False)

    def install_programs(self):
        distro_class = self.window.distro_class(self.window.gpu_vendor.lower())

        def toggle_programs():
            nonlocal distro_class
            print("Checking for toggled programs")

            to_install = self.window.get_active_toggle_btn()
            if to_install:
                programs = list()
                for _program in to_install:
                    program = _program.replace("-", "_").lower()
                    programs.append(program)
                distro_class.install_script(programs)

                if distro_class.__class__.__name__ == "Arch":
                    print("Installing toggled programs")
                    process = subprocess.Popen(
                        ("sh", self.window.current_path + "install.sh"),
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    process.stdin.write(b"Y\n")
                    process.wait()

                else:
                    print("Installing toggled programs")
                    process = subprocess.Popen(
                        ("pkexec", "sh", self.window.current_path + "install.sh"),
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    process.stdin.write(b"Y\n")
                    process.wait()

            distro_class.last_all()
            if os.path.isfile(self.window.current_path + "install.sh"):
                print("deleting install.sh")
                os.remove(self.window.current_path + "install.sh")

        toggle_programs()

        def install_certain_rel():
            nonlocal distro_class
            popout_programs = self.window.popout_programs
            print("Checking for certain program releases")
            if popout_programs:
                tag_names = list()
                proge_links = list()  # proton-ge download links
                for program in popout_programs:
                    store = popout_programs.get(program)[3]
                    cells_n = len(store)
                    for i in range(0, cells_n):
                        if list(store)[i][0]:
                            tag_names.append(list(store)[i][1])

                for json_object in self.window.releases_data:
                    tag_name = json_object.get("tag_name")
                    download_url = json_object.get("download_url")
                    if tag_name in tag_names:
                        proge_links.append(download_url)
                distro_class.proton_ge_all(proge_links)

        install_certain_rel()
        self.reset()
        print("DONE")

    def install(self, *args):
        thread = threading.Thread(target=self.install_programs)
        thread.start()


class Window(Gtk.ApplicationWindow):
    @property
    def distro_class(self):
        """
        Gets the appropiate class to install programs
        """

        def print_name(name):
            print("Your distro is/based on: " + name)

        if distro.like() == "debian":
            if distro.id() == "ubuntu":
                _distribution = installer.Ubuntu
                print_name(_distribution.__name__)
                return _distribution

        def distribution():
            _like = distro.like()
            _id = distro.id()
            if _like:
                return _like
            elif _id:
                return _id
            raise SystemError("Distribution not recognized")

        _distribution_class = getattr(installer, distribution().capitalize())
        print_name(_distribution_class.__name__)
        return _distribution_class

    @property
    def gpu_vendor(self):
        return info.GraphicsCard().vendor

    def __init__(self):
        Gtk.ApplicationWindow.__init__(self)
        self.set_urgency_hint(True)
        self.set_default_size(400, 100)
        self._app_init()

    def _app_init(self):
        self.variables()
        self.headerbar()
        self.body()
        self.menu_popover()
        self.set_gpu_vendor()

    def variables(self):
        self.handler = Handler(self)
        self.current_path = os.path.dirname(os.path.abspath(__file__)) + "/"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.current_path + "ui.glade")
        self.builder.connect_signals(self.handler)
        self.toggle_programs = {
            "Wine": None,
            "Lutris": None,
            "Steam": None,
            "vkBasalt": None,
            "Gamemode": None,
        }
        self.popout_programs = {
            "Proton-Ge": [
                "https://api.github.com/repos/GloriousEggroll/"
                + "proton-ge-custom/releases",
                None,  # button object
                None,  # version selector window
                None,  # GtkTreeView
            ]
        }
        self.brother_programs = {
            "Lutris": "Wine",
        }
        _checker = checker.All
        self.check_programs = {
            "Gamemode": _checker.gamemode_all(),
            "vkBasalt": _checker.vkbasalt_all(),
            "Proton-Ge": _checker.proton_ge(),
        }

    def headerbar(self):
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        self.set_titlebar(header_bar)

        self.menu_button = Gtk.MenuButton()
        icon = Gio.ThemedIcon(name="view-more")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.menu_button.add(image)
        header_bar.pack_end(self.menu_button)

    def body(self):
        vbox = Gtk.VBox()
        vbox.set_homogeneous(False)
        objects = [
            self.toggle_programs,
            self.popout_programs,
            self.handler,
            self.crate_rele_sel,  # release selector
            self.check_programs,  # installed porgrams
        ]

        flowbox = widgets.FlowBox(objects)
        vbox.pack_start(flowbox, False, True, 0)

        def do_buttons_box():
            button_reset = Gtk.Button("Reset")
            button_reset.connect("clicked", self.handler.reset)

            button_install = Gtk.Button("Install")
            button_install.connect("clicked", self.handler.install)

            do_buttons_box = Gtk.HBox()
            do_buttons_box.pack_start(button_reset, True, True, 0)
            do_buttons_box.pack_end(button_install, True, True, 0)
            return do_buttons_box

        vbox.pack_end(do_buttons_box(), False, False, 0)

        self.add(vbox)

    def get_active_toggle_btn(self):
        """
        Gets programs to install by checking if the
        toggle button is active or not.
        """
        programs = list()
        for button_obj in self.toggle_programs.values():
            if button_obj.get_active() and button_obj.get_sensitive():
                program_name = button_obj.get_name().replace("-", "_")
                programs.append(program_name)
        return programs

    def menu_popover(self):
        popover = self.builder.get_object("menu_popover")
        self.menu_button.set_popover(popover)

    def set_gpu_vendor(self):
        if self.gpu_vendor == "unknown":
            dialog = widgets.MessageDialog(
                self,
                title="Warning",
                message=(
                    "You will have to select ur gpu vendor manually",
                    "by clicking on the menu button and select it",
                    "form the combo button",
                ),
            )
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                dialog.destroy()
        else:
            select_vendor_button = self.builder.get_object("select_gpu_vendor")
            select_vendor_button.set_active_id(self.gpu_vendor)

    def crate_rele_sel(self, api_link, program_name):
        """
        Creates lutris like release selector for a specific program
        """
        self.releases_data = multi.get_release_data(api_link)
        selector = widgets.ReleaseSelector(
            program_name, self.releases_data, self.check_programs
        )
        return selector, selector.tree_view.store

    def show_all_(self):
        self.connect("destroy", self.stop)
        self.show_all()
        Gtk.main()

    def start(self):
        self.show_all_()

    def stop(self, *args):
        Gtk.main_quit()
