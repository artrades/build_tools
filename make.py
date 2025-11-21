#!/usr/bin/env python
# python 3.5
import os 
import sys
__dir__name__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__name__ + '/scripts')
sys.path.append(__dir__name__ + '/scripts/develop')
sys.path.append(__dir__name__ + '/scripts/develop/vendor')
sys.path.append(__dir__name__ + '/scripts/core_common')
sys.path.append(__dir__name__ + '/scripts/core_common/modules')
sys.path.append(__dir__name__ + '/scripts/core_common/modules/android')
import config
import base
import build_sln
import build_js
import build_server
import deploy
import make_common
import develop
import argparse



print("=" * 60)
print("1 PAUSE [make.py] base.check_python()")
print("=" * 60)
print("Press Enter to continue...")
#input()

base.check_python()

parser = argparse.ArgumentParser(description="options")
parser.add_argument("--build-only-branding", action="store_true")
args = parser.parse_args()

if (args.build_only_branding):
  base.set_env("OO_BUILD_ONLY_BRANDING", "1")

# parse configuration
config.parse()

base_dir = base.get_script_dir(__file__)

base.set_env("BUILD_PLATFORM", config.option("platform"))

# branding
if ("1" != base.get_env("OO_RUNNING_BRANDING")) and ("" != config.option("branding")):
  branding_dir = base_dir + "/../" + config.option("branding")

  if ("1" == config.option("update")):
    is_exist = True
    if not base.is_dir(branding_dir):
      is_exist = False
      base.cmd("git", ["clone", config.option("branding-url"), branding_dir])

    base.cmd_in_dir(branding_dir, "git", ["fetch"], True)

    if not is_exist or ("1" != config.option("update-light")):
      base.cmd_in_dir(branding_dir, "git", ["checkout", "-f", config.option("branch")], True)

    base.cmd_in_dir(branding_dir, "git", ["pull"], True)

  if base.is_file(branding_dir + "/build_tools/make.py"):
    base.check_build_version(branding_dir + "/build_tools")
    base.set_env("OO_RUNNING_BRANDING", "1")
    base.set_env("OO_BRANDING", config.option("branding"))
    base.cmd_in_dir(branding_dir + "/build_tools", "python", ["make.py"])
    exit(0)


print("=" * 60)
print("2 PAUSE [make.py] config.parse_defaults()")
print("=" * 60)
print("Press Enter to continue...")
#input()
# correct defaults (the branding repo is already updated)
config.parse_defaults()



print("=" * 60)
print("3 PAUSE [make.py] base.check_build_version(base_dir)")
print("=" * 60)
print("Press Enter to continue...")
input()
base.check_build_version(base_dir)

# update
if ("1" == config.option("update")):
  repositories = base.get_repositories()
  base.update_repositories(repositories)



print("=" * 60)
print("4 PAUSE [make.py] base.configure_common_apps()")
print("=" * 60)
print("Press Enter to continue...")
input()
base.configure_common_apps()

# developing...
develop.make()

# check only js builds
if ("1" == base.get_env("OO_ONLY_BUILD_JS")):
  build_js.make()
  exit(0)

#base.check_tools()


print("=" * 60)
print("5 PAUSE [make.py] core 3rdParty  make_common.make()")
print("=" * 60)
print("Press Enter to continue...")
input()
# core 3rdParty
make_common.make()

# build updmodule for desktop (only for windows version)
if config.check_option("module", "desktop"):
  config.extend_option("qmake_addon", "URL_WEBAPPS_HELP=https://download.onlyoffice.com/install/desktop/editors/help/v" + base.get_env('PRODUCT_VERSION') + "/apps")

  if "windows" == base.host_platform():
    config.extend_option("config", "updmodule")
    base.set_env("DESKTOP_URL_UPDATES_MAIN_CHANNEL", "https://download.onlyoffice.com/install/desktop/editors/windows/onlyoffice/appcast.json")
    base.set_env("DESKTOP_URL_UPDATES_DEV_CHANNEL", "https://download.onlyoffice.com/install/desktop/editors/windows/onlyoffice/appcastdev.json")
    base.set_env("DESKTOP_URL_INSTALL_CHANNEL", "https://download.onlyoffice.com/install/desktop/editors/windows/distrib/onlyoffice/<file>")
    base.set_env("DESKTOP_URL_INSTALL_DEV_CHANNEL", "https://download.onlyoffice.com/install/desktop/editors/windows/onlyoffice/onlineinstallerdev/<file>")


print("=" * 60)
print("6 PAUSE [make.py] build_sln.make()")
print("=" * 60)
print("Press Enter to continue...")
input()
# build
build_sln.make()


print("=" * 60)
print("7 PAUSE [make.py] build_js.make()")
print("=" * 60)
print("Press Enter to continue...")
input()
# js
build_js.make()


print("=" * 60)
print("8 PAUSE [make.py] build_server.make()")
print("=" * 60)
print("Press Enter to continue...")
input()
#server
build_server.make()

# deploy
deploy.make()

