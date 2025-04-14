import gettext
import locale

translation = gettext.translation("WCount", "po", fallback=True)
_, ngettext = translation.gettext, translation.ngettext

LOCALES = {
    ("ru_RU", "UTF-8"): gettext.translation("WCount", "po", ["ru"]),
    ("en_US", "UTF-8"): gettext.NullTranslations(),
}


def _(text):
    return LOCALES[locale.getlocale()].gettext(text)

def ngettext(text, textn, n):
    return LOCALES[locale.getlocale()].ngettext(text, textn, n)

while line := input(_("enter string: ")):
    wrd = line.split()
    N = len(wrd)
    for loc in LOCALES:
        locale.setlocale(locale.LC_ALL, loc)
        print(ngettext("Entered {} word", "Entered {} words", N).format(N))

