import contextlib
import io
import json
import os
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from mathcat.cli import main
from mathcat.display import display_png
from mathcat.legend import compose_legend, greek_in, notation_in
from mathcat.render import FormulaError, render_png
from mathcat.server import Handler


class RenderTests(unittest.TestCase):
    def test_euler_is_png(self):
        png = render_png(r"e^{i\pi}+1=0")
        self.assertTrue(png.startswith(b"\x89PNG"))

    def test_dollars_are_optional(self):
        bare = render_png(r"E=mc^2")
        wrapped = render_png(r"$E=mc^2$")
        self.assertTrue(bare.startswith(b"\x89PNG"))
        self.assertTrue(wrapped.startswith(b"\x89PNG"))

    def test_environment_is_rejected(self):
        with self.assertRaises(FormulaError):
            render_png(r"\begin{matrix}a\end{matrix}")

    def test_empty_is_rejected(self):
        with self.assertRaises(FormulaError):
            render_png("   ")


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.httpd.server_address
        cls.base = f"http://{host}:{port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_health(self):
        with urllib.request.urlopen(self.base + "/health") as response:
            body = json.loads(response.read().decode())
        self.assertEqual(body["ok"], True)

    def test_post_png(self):
        payload = json.dumps({"tex": r"e^{i\pi}+1=0"}).encode()
        request = urllib.request.Request(
            self.base + "/png",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            png = response.read()
            self.assertEqual(response.headers.get("Content-Type"), "image/png")
        self.assertTrue(png.startswith(b"\x89PNG"))

    def test_bad_formula_is_400(self):
        payload = json.dumps({"tex": r"\begin{align}a\end{align}"}).encode()
        request = urllib.request.Request(
            self.base + "/png",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        self.assertEqual(caught.exception.code, 400)


class LegendTests(unittest.TestCase):
    def test_order_and_uniqueness(self):
        found = greek_in(r"\alpha+\pi+\alpha+\beta")
        self.assertEqual([item[0] for item in found], ["alpha", "pi", "beta"])
        self.assertEqual([item[2] for item in found], ["alpha", "pi", "beta"])

    def test_same_letter_keeps_its_color(self):
        first = greek_in(r"\pi")[0][3]
        later = greek_in(r"\sigma+\pi")[1][3]
        self.assertEqual(first, later)
        self.assertEqual(greek_in(r"\pi")[0][3], greek_in(r"\Pi")[0][3])

    def test_ledger_is_a_larger_png(self):
        tex = r"e^{i\pi}+1=0"
        plain = render_png(tex)
        card = compose_legend(tex, plain)
        self.assertTrue(card.startswith(b"\x89PNG"))
        self.assertGreater(len(card), len(plain))

    def test_no_notation_leaves_the_formula(self):
        tex = r"E=mc"
        plain = render_png(tex)
        self.assertEqual(compose_legend(tex, plain), plain)

    def test_scripts_alone_get_a_ledger(self):
        tex = r"E=mc^2"
        plain = render_png(tex)
        self.assertGreater(len(compose_legend(tex, plain)), len(plain))

    def test_accents_and_scripts_are_spoken(self):
        spoken = [item[2] for item in notation_in(r"\hat{x}_i^2+\bar{y}+A^{-1}+f(x)^3")]
        self.assertEqual(
            spoken,
            [
                "$x$ hat",
                r"$\hat{x}$ sub $i$",
                r"$\hat{x}$ squared",
                "$y$ bar",
                "$A$ inverse",
                "$f(x)$ cubed",
            ],
        )

    def test_limits_read_from_and_to(self):
        spoken = [item[2] for item in notation_in(r"\int_{0}^{1} x\,dx + \lim_{n\to\infty} a_n")]
        self.assertEqual(
            spoken,
            [r"$\int$ from $0$", r"$\int$ to $1$", r"$\lim$ as $n\to\infty$", "$a$ sub $n$"],
        )

    def test_notes_alone_make_a_card(self):
        tex = r"E=mc"
        plain = render_png(tex)
        card = compose_legend(tex, plain, legend=False, notes=["Mass is energy at rest."])
        self.assertGreater(len(card), len(plain))
        self.assertEqual(compose_legend(tex, plain, legend=False, notes=["  "]), plain)

    def test_note_with_broken_mathtext_still_renders(self):
        tex = r"x_i"
        card = compose_legend(tex, render_png(tex), notes=["costs $5 and $\\frac{"])
        self.assertTrue(card.startswith(b"\x89PNG"))

    def test_notation_is_listed_once(self):
        self.assertEqual(len(notation_in(r"x_i+x_i+x_{i}")), 1)


class CliTests(unittest.TestCase):
    def test_output_file(self):
        path = os.path.join(self.id().replace(".", "_") + ".png")
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main(["--local", "-o", path, r"E=mc^2"])
            self.assertEqual(code, 0)
            self.assertEqual(out.getvalue().strip(), os.path.abspath(path))
            with open(path, "rb") as handle:
                self.assertTrue(handle.read(8).startswith(b"\x89PNG"))
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_iterm_protocol_matches_imgcat(self):
        png = render_png(r"E=mc^2")
        buf = io.BytesIO()
        display_png(png, "iterm", buf)
        data = buf.getvalue()
        self.assertTrue(data.startswith(b"\033]1337;File=inline=1;"))
        self.assertIn(b"\a", data)


if __name__ == "__main__":
    unittest.main()
