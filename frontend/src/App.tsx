import React, { useState, useEffect } from 'react';
import { Upload, Music, BarChart2, Library, ChevronRight, Check } from 'lucide-react';
import './index.css';

const PROCESSING_STEPS = [
  "IMAGE RECEIVED",
  "EXTRACTING FEATURES",
  "SCALING FEATURES",
  "FINDING NEAREST NEIGHBOURS",
  "CLASSIFYING GENRE",
  "RESULT READY"
];

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState(-1);
  const [predictionResult, setPredictionResult] = useState<any>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);
    
    setPredictionResult(null);
    setIsProcessing(true);
    setProcessingStep(0);

    let currentStep = 0;
    const interval = setInterval(() => {
      currentStep++;
      if (currentStep < PROCESSING_STEPS.length - 1) {
        setProcessingStep(currentStep);
      }
    }, 600);

    try {
      const formData = new FormData();
      formData.append('image', selectedFile);

      const response = await fetch('http://localhost:8000/predict', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Prediction failed: ${response.status} ${errorText}`);
      }

      const data = await response.json();
      
      setTimeout(() => {
        clearInterval(interval);
        setProcessingStep(PROCESSING_STEPS.length - 1);
        setTimeout(() => {
          setPredictionResult(data);
          setIsProcessing(false);
        }, 800);
      }, Math.max(0, 2000 - (currentStep * 600))); // Ensure minimum animation time

    } catch (error: any) {
      console.error('Error during prediction:', error);
      clearInterval(interval);
      setIsProcessing(false);
      alert(`Failed to process image: ${error.message}`);
    }
  };

  return (
    <div style={{ width: '100%', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Navigation */}
      <header className="container">
        <nav className="nav">
          <a href="/" className="nav-brand flex-center gap-sm">
            <Music size={24} />
            Playlify
          </a>
          <button className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '0.875rem' }}>
            About the Research
          </button>
        </nav>
      </header>

      {/* Main Content */}
      <main className="container" style={{ flex: 1, paddingBottom: 'var(--spacing-xl)' }}>
        
        {/* Hero Section */}
        <section className="section flex-col flex-center" style={{ textAlign: 'center', maxWidth: '800px', margin: '0 auto', gap: 'var(--spacing-md)' }}>
          <h1 className="text-display" style={{ marginBottom: 0 }}>SEE THE GENRE<br/>BEHIND THE COVER.</h1>
          <p className="text-body-large" style={{ color: 'var(--color-teal-waters)', opacity: 0.8, maxWidth: '600px' }}>
            A visual research laboratory exploring the relationship between album artwork and musical genre classification using machine learning.
          </p>
        </section>

        {/* Upload Area */}
        <section className="flex-center" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <div className="upload-zone" style={{ width: '100%', maxWidth: '600px' }}>
            <input type="file" accept="image/*" onChange={handleFileUpload} />
            <Upload size={48} color="var(--color-teal-waters)" />
            <div style={{ textAlign: 'center' }}>
              <h3 className="text-h3" style={{ marginBottom: 'var(--spacing-xs)' }}>Upload Album Cover</h3>
              <p className="text-body" style={{ color: 'var(--color-teal-waters)', opacity: 0.7 }}>
                Drag and drop your image here, or click to browse.
              </p>
            </div>
            <div className="btn btn-primary" style={{ marginTop: 'var(--spacing-sm)' }}>
              Select Image <ChevronRight size={18} />
            </div>
          </div>
        </section>

        {/* Processing State */}
        {(isProcessing || (previewUrl && !predictionResult)) && (
          <div className="animate-fade-in flex-center flex-col gap-lg" style={{ marginBottom: 'var(--spacing-xl)' }}>
             <div style={{ 
                width: '300px', 
                height: '300px', 
                backgroundColor: 'var(--color-morning-mist)', 
                borderRadius: 'var(--radius-md)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                boxShadow: 'var(--shadow-hover)',
                overflow: 'hidden',
                position: 'relative'
              }}>
                {previewUrl && <img src={previewUrl} alt="Preview" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />}
                
                {isProcessing && (
                   <div style={{ position: 'absolute', inset: 0, backgroundColor: 'rgba(32, 70, 84, 0.7)', display: 'flex', flexDirection: 'column', padding: 'var(--spacing-xl)', justifyContent: 'center' }}>
                      <div className="flex-col gap-md">
                        {PROCESSING_STEPS.map((step, idx) => {
                          const isActive = idx === processingStep;
                          const isCompleted = idx < processingStep;
                          const isPending = idx > processingStep;

                          if (isPending) return null;

                          return (
                            <div key={step} className={`step-item ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}>
                              {isCompleted ? <Check size={16} /> : <div className="pulse-indicator"></div>}
                              {step}
                            </div>
                          );
                        })}
                      </div>
                   </div>
                )}
             </div>
          </div>
        )}

        {/* Results Section */}
        {predictionResult && !isProcessing && (
          <div className="animate-fade-in">
            <div className="grid-2" style={{ marginBottom: 'var(--spacing-xl)' }}>
              
              {/* Prediction Panel */}
              <div className="panel-dark flex-col gap-lg">
                <div>
                  <p className="text-small" style={{ opacity: 0.8, textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 'var(--spacing-xs)' }}>The Model Predicts</p>
                  <h2 className="text-display" style={{ marginBottom: 0, color: 'var(--color-spring-meadow)' }}>
                    {predictionResult.prediction.genre.toUpperCase()}
                  </h2>
                  <p className="text-body-large" style={{ opacity: 0.9 }}>
                    {(predictionResult.prediction.confidence * 100).toFixed(1)}% Confidence
                  </p>
                </div>
                
                <div style={{ marginTop: 'auto' }}>
                  <h4 className="text-body-large" style={{ marginBottom: 'var(--spacing-md)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <BarChart2 size={20} /> Probability Distribution
                  </h4>
                  
                  <div className="flex-col gap-sm">
                    {Object.entries(predictionResult.prediction.all_probabilities || {})
                      .sort(([, a]: any, [, b]: any) => b - a)
                      .slice(0, 3)
                      .map(([genre, prob]: any, idx) => (
                      <div key={genre}>
                        <div className="flex-center" style={{ justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.875rem', opacity: idx === 0 ? 1 : 0.8 }}>
                          <span>{String(genre)}</span>
                          <span>{(prob * 100).toFixed(1)}%</span>
                        </div>
                        <div className="bar-chart-container bar-chart-container-light">
                          <div className={`bar-chart-fill ${idx === 0 ? 'highlight' : ''}`} style={{ width: `${Math.max(2, prob * 100)}%`, backgroundColor: idx === 0 ? 'var(--color-spring-meadow)' : 'rgba(247, 249, 225, 0.4)' }}></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Methodology / Uploaded Image View */}
              <div className="panel-secondary flex-col gap-lg" style={{ justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
                 <div style={{ width: '250px', height: '250px', backgroundColor: 'var(--color-morning-mist)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: 'var(--shadow-subtle)', overflow: 'hidden' }}>
                    {previewUrl ? (
                      <img src={previewUrl} alt="Analyzed artwork" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    ) : (
                      <span style={{ opacity: 0.5 }}>Image Preview</span>
                    )}
                 </div>
                 <div>
                    <h3 className="text-h3">Visual Analysis Complete</h3>
                    <p className="text-body" style={{ opacity: 0.8 }}>Extracted feature vectors were passed through our MLP neural network and PCA dimensionality reduction.</p>
                 </div>
              </div>
            </div>

            {/* Similar Albums Section */}
            {predictionResult.similar_albums && predictionResult.similar_albums.length > 0 && (
              <section className="flex-col gap-lg animate-fade-in" style={{ animationDelay: '0.3s' }}>
                <div className="flex-center" style={{ justifyContent: 'space-between', borderBottom: '1px solid rgba(32, 70, 84, 0.1)', paddingBottom: 'var(--spacing-md)' }}>
                  <h3 className="text-h2" style={{ marginBottom: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Library size={28} /> Visual Nearest Neighbors
                  </h3>
                  <span className="text-body" style={{ color: 'var(--color-teal-waters)', opacity: 0.7 }}>k={predictionResult.similar_albums.length} albums</span>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 'var(--spacing-lg)' }}>
                  {predictionResult.similar_albums.map((album: any, idx: number) => (
                    <div key={idx} className="card" style={{ padding: 'var(--spacing-md)' }}>
                      <div style={{ width: '100%', aspectRatio: '1/1', backgroundColor: 'var(--color-glacial-sky)', borderRadius: 'var(--radius-sm)', marginBottom: 'var(--spacing-md)', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
                        {album.image_url ? (
                           <img src={album.image_url} alt={`Album ${album.album_index}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                        ) : (
                          <span style={{ opacity: 0.5 }}>Artwork</span>
                        )}
                      </div>
                      <h4 className="text-body-large" style={{ marginBottom: '4px' }}>{album.genre}</h4>
                      <p className="text-small" style={{ opacity: 0.7 }}>dist: {album.distance.toFixed(3)}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </main>
      
      {/* Footer */}
      <footer style={{ borderTop: '1px solid rgba(32, 70, 84, 0.1)', padding: 'var(--spacing-lg) 0', marginTop: 'auto' }}>
        <div className="container flex-center" style={{ justifyContent: 'space-between' }}>
          <p className="text-small" style={{ opacity: 0.6 }}>Playlify Research • Machine Learning Visualization</p>
          <div className="flex-center gap-md">
            <span style={{ width: '16px', height: '16px', borderRadius: '50%', backgroundColor: 'var(--color-morning-mist)', border: '1px solid var(--color-teal-waters)' }}></span>
            <span style={{ width: '16px', height: '16px', borderRadius: '50%', backgroundColor: 'var(--color-spring-meadow)' }}></span>
            <span style={{ width: '16px', height: '16px', borderRadius: '50%', backgroundColor: 'var(--color-teal-waters)' }}></span>
            <span style={{ width: '16px', height: '16px', borderRadius: '50%', backgroundColor: 'var(--color-glacial-sky)' }}></span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
