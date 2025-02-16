from manim import *

class SalaryEvolution(Scene):
    def construct(self):
        intro_group = self.introduction()
        self.play(FadeOut(intro_group))
        years = [
            1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 
            2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 
            2016, 2017, 2018, 2019, 2020, 2021, 2022
        ]
        salaries = [
            100.0, 100.5, 100.9, 103.4, 105.2, 106.1, 106.3, 105.6, 105.1, 106.1,
            106.4, 108.7, 108.0, 106.3, 107.6, 105.8, 104.8, 103.5, 104.0, 105.1,
            105.4, 105.6, 105.4, 104.6, 106.6, 104.7, 103.4
        ]
        title = "Evolution of Salaries of French Executives (INSEE)"
        self.content(years, salaries, title)
        self.wait(3)


    def content(self, years, salaries, title):
        axes = Axes(
            x_range=[years[0], years[-1], 2],
            y_range=[95, 110, 2],
            axis_config={"include_numbers": True, "font_size": 24},
            x_axis_config={"label_direction": DOWN},
            y_axis_config={"label_direction": LEFT}
        ).shift(DOWN * 0.5)
        
        x_label = axes.get_x_axis_label("Year", direction=RIGHT, buff=1.25)
        y_label = axes.get_y_axis_label("Salary Index", direction=UP, buff=0.25)
        
        graph = axes.plot_line_graph(
            years, salaries, line_color=BLUE, add_vertex_dots=True
        )

        title = Text(title, font_size=28).to_edge(UP)
        self.play(Create(axes), Write(x_label), Write(y_label), Write(title))
        for i in range(len(years) - 1):
            self.play(Create(Line(
                axes.c2p(years[i], salaries[i]), 
                axes.c2p(years[i + 1], salaries[i + 1]), 
                color=BLUE
            )), run_time=0.4)
            self.play(Create(Dot(axes.c2p(years[i + 1], salaries[i + 1]), color=BLUE)), run_time=0.2)

        # Hold the screen for a while
        self.wait(2)

        # # Fade out everything
        # self.play(FadeOut(axes), FadeOut(x_label), FadeOut(y_label), FadeOut(title), FadeOut(graph))

    def introduction(self):
        header = Tex("French Salaries")
        header.set_width(8)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.5, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.5, 0]
        line = Line(from_pos, to_pos)
        writer = Tex("Created by Ptolémé")
        writer_pos = [(line.get_left()[0] + line.get_right()[0]) / 2, line.get_bottom()[1] - 1, 0]
        writer.move_to(writer_pos)
        
        self.play(Write(header), Write(line))
        self.wait(0.5)
        self.play(Transform(header, Tex("From INSEE data")))
        self.play(Write(writer))
        self.wait(1.5)
        
        return VGroup(header, writer, line)
