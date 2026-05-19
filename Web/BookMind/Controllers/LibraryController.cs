using Microsoft.AspNetCore.Mvc;

namespace BookMind.Controllers;

public class LibraryController : Controller
{
    public IActionResult Index()
    {
        return View();
    }
}
