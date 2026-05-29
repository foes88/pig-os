"""
Addon routers mount here.

To add FCR Addon router:
  from app.addons import fcr   # triggers AddonRegistry.register()
  # That's it — main.py reads AddonRegistry and mounts automatically.

Future Addon packages to import:
  from app.addons import fcr      # ADDON_FCR   → /addons/fcr/*
  from app.addons import health   # ADDON_HEALTH → /addons/health/*
  from app.addons import market   # ADDON_MARKET → /addons/market/*
  from app.addons import breeding # ADDON_BREEDING → /addons/breeding/*
  from app.addons import biosec   # ADDON_BIOSECURITY → /addons/biosecurity/*
"""
