image movie1 = Movie(play="images/movie1.webm")

image movie3 = Movie(play="images/movie3.webm")

image movie4 = Movie(play="images/movie4.webm")

init python:
    gallery = Gallery()

    gallery.button("catchingbullet") 
    gallery.image("images/catchingbullet.png")
    gallery.condition("persistent.seen_the_bullet") 

    gallery.button("movie1") 
    gallery.image("movie1")
    gallery.condition("persistent.seen_movie1 == 1")

    gallery.button("movie3") 
    gallery.image("movie3")
    gallery.condition("persistent.seen_movie3 == 1")

    gallery.button("movie4") 
    gallery.image("movie4")
    gallery.condition("persistent.seen_movie4 == 1")

screen gallery():
    tag menu

    text _("When in a cutscene, click anywhere to stop it") xalign 0.5 yalign 1.0

    textbutton "Return" action [ Play("music", "audio/main-theme.mp3"), Return()] xalign 0.5 yalign 0.88

    hbox:
        xalign 0.5
        yalign 0.5
        spacing 30
        grid 2 2:
            add gallery.make_button(name="catchingbullet",unlocked="images/gallery stuff/catchingbullet.png",locked="images/gallery stuff/locked.png") 
            add gallery.make_button(name="movie1",unlocked="images/gallery stuff/movie1.png",locked="images/gallery stuff/locked.png")
            add gallery.make_button(name="movie3",unlocked="images/gallery stuff/movie3.png",locked="images/gallery stuff/locked.png")
            add gallery.make_button(name="movie4",unlocked="images/gallery stuff/movie4.png",locked="images/gallery stuff/locked.png")
            spacing 10
