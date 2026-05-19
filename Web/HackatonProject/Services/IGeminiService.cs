using HackatonProject.Models;
using System.Threading.Tasks;

namespace HackatonProject.Services
{
    public interface IGeminiService
    {
        Task<RecipeAnalysisResult?> AnalyzeImageAsync(byte[] imageBytes);
        Task<RecipeAnalysisResult?> AnalyzeLinkAsync(string url);
        Task<Product?> GetBestProductMatchAsync(string ingredientName, List<Product> availableProducts);
    }
}
