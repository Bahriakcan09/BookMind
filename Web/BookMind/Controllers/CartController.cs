using Microsoft.AspNetCore.Mvc;

namespace BookMind.Controllers;

public class CartController : Controller
{
    public IActionResult Index()
    {
        return View();
    }

    public IActionResult Checkout()
    {
        return View();
    }

    public IActionResult Orders()
    {
        return View();
    }
}
