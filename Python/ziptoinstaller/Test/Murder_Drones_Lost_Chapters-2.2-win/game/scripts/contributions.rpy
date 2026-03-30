image contributions = "images/contributions.png"

screen contributions():
    tag menu

    add "contributions"

    text _("The Vietnamese (WIP) translation was kindly made by dido2000/dảk gaming, thank you so much for helping out!") xalign 0.5 yalign 0.3

    text _("Kinetic Text Tags Ren'Py Module is made by Daniel Westfall, thank you for making my life way easier!") xalign 0.5 yalign 0.4

    text _("BobCAchievements Code is made by Bob Conway, thank you for making the achivement system I use!") xalign 0.5 yalign 0.5

    text _("All the tutorials I watched and all the people on Reddit and Discord that helped me, thank you so much!") xalign 0.5 yalign 0.6

    text _("And thank YOU for playing the game <3") xalign 0.5 yalign 0.7

    textbutton "Return" action [ Play("music", "audio/main-theme.mp3"), Return()] xalign 0.5 yalign 0.88