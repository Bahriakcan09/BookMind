using HackatonProject.Models;
using HackatonProject.Services;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;

namespace HackatonProject.Controllers
{
    public class RecipeController : Controller
    {
        private readonly IGeminiService _geminiService;
        private readonly IFirebaseService _firebaseService;

        public RecipeController(IGeminiService geminiService, IFirebaseService firebaseService)
        {
            _geminiService = geminiService;
            _firebaseService = firebaseService;
        }

        [HttpGet]
        public IActionResult Index() => View();

        [HttpPost]
        public async Task<IActionResult> Analyze(IFormFile? recipeImage, string? recipeLink)
        {
            RecipeAnalysisResult? result = null;

            if (recipeImage != null && recipeImage.Length > 0)
            {
                using var ms = new MemoryStream();
                await recipeImage.CopyToAsync(ms);
                result = await _geminiService.AnalyzeImageAsync(ms.ToArray());
            }
            else if (!string.IsNullOrEmpty(recipeLink))
            {
                result = await _geminiService.AnalyzeLinkAsync(recipeLink);
            }

            if (result != null)
            {
                var products = await _firebaseService.GetProductsAsync();
                foreach (var ingredient in result.Ingredients)
                {
                    // AI-powered matching
                    ingredient.MatchedProduct = await _geminiService.GetBestProductMatchAsync(ingredient.Name, products);
                }
                return View("Result", result);
            }

            ViewBag.Error = "Analiz başarısız oldu. Lütfen tekrar deneyin.";
            return View("Index");
        }

        [HttpPost]
        public IActionResult UpdatePortion(RecipeAnalysisResult model, int portions)
        {
            // Calculate new amounts based on portions (baseline is 1 portion)
            foreach (var ing in model.Ingredients)
            {
                ing.Amount *= portions;
            }
            return PartialView("_IngredientList", model.Ingredients);
        }
    }
}
