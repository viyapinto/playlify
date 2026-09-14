import React, { useState } from 'react';
import { Upload, BarChart2, Library, ChevronRight, Check, AlertCircle } from 'lucide-react';
import ResearchVisualizations from './components/ResearchVisualizations';
import './index.css';

const PROCESSING_STEPS = [
  "IMAGE RECEIVED",
  "EXTRACTING VISUAL FEATURES",
  "COMPRESSING FEATURES",
  "FINDING NEAREST ALBUMS",
  "PREDICTING",
  "RESULT"
];

function App() {
  const [, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState(-1);
  const [predictionResult, setPredictionResult] = useState<any>(null);
  const [kValue] = useState(10);
  const [error, setError] = useState<string | null>(null);
  const [isColdStart, setIsColdStart] = useState(false);

  const processFile = async (selectedFile: File) => {
    setFile(selectedFile);
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);
    
    setPredictionResult(null);
    setError(null);
    setIsProcessing(true);
    setProcessingStep(0);
    setIsColdStart(false);

    const coldStartTimeout = setTimeout(() => {
      setIsColdStart(true);
    }, 4000);

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
      formData.append('k', kValue.toString());

      const rawApiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
      const apiUrl = rawApiUrl.replace(/\/$/, '');
      const response = await fetch(`${apiUrl}/predict`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        clearTimeout(coldStartTimeout);
        let errorMessage = `Prediction failed: ${response.status}`;
        try {
          const errorJson = await response.json();
          if (errorJson.detail) errorMessage = errorJson.detail;
        } catch (e) {
          // Fallback if not valid JSON
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      
      setTimeout(() => {
        clearTimeout(coldStartTimeout);
        clearInterval(interval);
        setProcessingStep(PROCESSING_STEPS.length - 1);
        setTimeout(() => {
          setPredictionResult(data);
          setIsProcessing(false);
        }, 800);
      }, Math.max(0, 2000 - (currentStep * 600))); // Ensure minimum animation time

    } catch (error: any) {
      console.error('Error during prediction:', error);
      clearTimeout(coldStartTimeout);
      clearInterval(interval);
      setIsProcessing(false);
      
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        setError('Failed to connect to the backend server. Please ensure the Python API is running.');
      } else {
        setError(error.message);
      }
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) return;
    await processFile(selectedFile);
  };

  const handleExampleClick = async (filename: string) => {
    try {
      const response = await fetch(`/examples/${filename}`);
      const blob = await response.blob();
      const file = new File([blob], filename, { type: blob.type });
      await processFile(file);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) {
      console.error(e);
      setError("Failed to load example image.");
    }
  };

  return (
    <div style={{ width: '100%', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Navigation */}
      <header className="container">
        <nav className="nav">
          <a href="/" className="nav-brand flex-center gap-sm">
            Playlify
          </a>
          <div className="flex-center gap-sm" style={{ flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            <button 
              className="btn btn-secondary" 
              style={{ padding: '8px 16px', fontSize: '0.875rem' }}
              onClick={() => document.getElementById('about-research')?.scrollIntoView({ behavior: 'smooth' })}
            >
              About the Research
            </button>
            <button 
              className="btn btn-secondary" 
              style={{ padding: '8px 16px', fontSize: '0.875rem' }}
              onClick={() => document.getElementById('model-reveals')?.scrollIntoView({ behavior: 'smooth' })}
            >
              What the Model Reveals
            </button>
          </div>
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
        {error && (
          <div className="animate-fade-in" style={{ maxWidth: '600px', margin: '0 auto var(--spacing-lg)', padding: 'var(--spacing-md)', backgroundColor: 'rgba(220, 53, 69, 0.1)', border: '1px solid rgba(220, 53, 69, 0.3)', borderRadius: 'var(--radius-sm)', color: '#d32f2f', textAlign: 'center' }}>
            <p className="text-body-large" style={{ margin: 0 }}><strong>Oops!</strong> {error}</p>
          </div>
        )}
        <section className="flex-col flex-center" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <div className="upload-zone" style={{ width: '100%', maxWidth: '600px', position: 'relative' }}>
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
          
          {/* Try an Example */}
          <div style={{ marginTop: 'var(--spacing-xl)', textAlign: 'center', width: '100%' }}>
            <p className="text-small" style={{ opacity: 0.6, marginBottom: 'var(--spacing-md)' }}>Don't have an image? Try an example:</p>
            <div className="flex-center gap-md" style={{ flexWrap: 'wrap' }}>
              {[
                { file: 'example_3.jpg', type: 'Custom', label: 'Example 3' },
                { file: 'example_1.jpg', type: 'Custom', label: 'Example 1' },
                { file: 'example_2.jpg', type: 'Custom', label: 'Example 2' },
                { file: 'example_4.jpg', type: 'Custom', label: 'Example 4' },
                { file: 'example_5.jpg', type: 'Custom', label: 'Example 5' }
              ].map((ex) => (
                <div 
                  key={ex.file}
                  onClick={() => handleExampleClick(ex.file)}
                  style={{ 
                    cursor: 'pointer', 
                    width: '60px', 
                    height: '60px',
                    borderRadius: 'var(--radius-sm)',
                    overflow: 'hidden',
                    border: '2px solid transparent',
                    boxShadow: 'var(--shadow-subtle)',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseOver={(e) => e.currentTarget.style.borderColor = 'var(--color-teal-waters)'}
                  onMouseOut={(e) => e.currentTarget.style.borderColor = 'transparent'}
                  title={`${ex.type} Example: ${ex.label}`}
                >
                  <img src={`/examples/${ex.file}`} alt={ex.label} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Processing State */}
        {(isProcessing || (previewUrl && !predictionResult)) && (
          <div className="animate-fade-in flex-center flex-col gap-lg" style={{ marginBottom: 'var(--spacing-xl)' }}>
             <div style={{ 
                width: '100%', 
                maxWidth: '300px',
                aspectRatio: '1/1', 
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

             {isColdStart && isProcessing && (
               <div className="animate-fade-in" style={{ width: '100%', maxWidth: '300px', marginTop: 'var(--spacing-sm)', padding: 'var(--spacing-md)', backgroundColor: 'var(--color-glacial-sky)', borderRadius: 'var(--radius-sm)', borderLeft: '4px solid var(--color-teal-waters)' }}>
                 <p className="text-small" style={{ margin: 0, color: 'var(--color-obsidian-night)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                   <AlertCircle size={16} color="var(--color-teal-waters)" />
                   <span>Waking up the prediction server. This may take up to 50 seconds.</span>
                 </p>
               </div>
             )}
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
                 <div style={{ width: '100%', maxWidth: '250px', aspectRatio: '1/1', backgroundColor: 'var(--color-morning-mist)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: 'var(--shadow-subtle)', overflow: 'hidden' }}>
                    {previewUrl ? (
                      <img src={previewUrl} alt="Analyzed artwork" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    ) : (
                      <span style={{ opacity: 0.5 }}>Image Preview</span>
                    )}
                 </div>
                 <div>
                    <h3 className="text-h3">Visual Analysis Complete</h3>
                    <p className="text-body" style={{ opacity: 0.8 }}>Playlify found visually closest albums to help predict the genre.</p>
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
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 200px), 1fr))', gap: 'var(--spacing-lg)' }}>
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

        {/* Visual Story / Research Section */}
          <section id="about-research" className="section flex-col animate-fade-in" style={{ 
            padding: 'var(--spacing-xxl)', 
            marginTop: 'var(--spacing-xl)',
            backgroundColor: 'rgba(32, 70, 84, 0.03)',
            borderRadius: 'var(--radius-xl)',
            border: '1px solid rgba(32, 70, 84, 0.1)'
          }}>
            {/* Playlify Intro (Playlify Native Style) */}
            <div className="flex-col gap-lg" style={{ maxWidth: '900px', margin: '0 auto var(--spacing-xxl)', width: '100%', textAlign: 'center' }}>
              
              <div style={{ marginBottom: 'var(--spacing-lg)' }}>
                <h2 className="text-display" style={{ marginBottom: 'var(--spacing-sm)' }}>What is Playlify?</h2>
                <p className="text-body-large" style={{ opacity: 0.8, maxWidth: '650px', margin: '0 auto' }}>
                  Playlify is a machine learning research application that explores a simple question: <br/>
                  <strong style={{ color: 'var(--color-teal-waters)' }}>can an album cover reveal something about the music it represents?</strong>
                </p>
              </div>

              <div className="grid-2" style={{ gap: 'var(--spacing-lg)', alignItems: 'stretch' }}>
                
                {/* Card 1: How it works */}
                <div className="card flex-col" style={{ 
                  textAlign: 'left', 
                  padding: 'var(--spacing-xxl)', 
                  backgroundColor: 'var(--color-glacial-sky)',
                  border: '1px solid var(--color-teal-waters)',
                  borderRadius: '32px',
                  boxShadow: 'none'
                }}>
                  <h3 className="text-display" style={{ color: 'var(--color-teal-waters)', marginBottom: 'var(--spacing-md)', fontSize: '2rem', lineHeight: 1.2 }}>
                    How it works
                  </h3>
                  <div className="text-body" style={{ opacity: 0.9, lineHeight: 1.6, flexGrow: 1, margin: 0 }}>
                    <p style={{ margin: 0 }}>
                      Upload an album cover and Playlify analyses its visual features to predict its <strong>music genre</strong> and find <strong>album covers that look visually similar</strong>. Behind the interface, machine learning techniques transform artwork into numerical visual representations, classify the artwork, and compare it with other albums in the dataset.
                    </p>
                  </div>
                </div>

                {/* Card 2: What is it trying to find? */}
                <div className="card flex-col" style={{ 
                  textAlign: 'left', 
                  padding: 'var(--spacing-xxl)', 
                  backgroundColor: 'var(--color-spring-meadow)',
                  border: '1px solid var(--color-teal-waters)',
                  borderRadius: '32px',
                  boxShadow: 'none'
                }}>
                  <h3 className="text-display" style={{ color: 'var(--color-teal-waters)', marginBottom: 'var(--spacing-md)', fontSize: '2rem', lineHeight: 1.2 }}>
                    What is Playlify trying to find?
                  </h3>
                  <div className="text-body" style={{ opacity: 0.9, lineHeight: 1.6, flexGrow: 1, margin: 0 }}>
                    <p style={{ margin: '0 0 var(--spacing-sm) 0' }}>
                      The goal is not to prove that a particular visual style <em>is</em> a genre. Instead, Playlify investigates <strong>how much information about music genre can actually be found in album artwork alone</strong>.
                    </p>
                    <p style={{ margin: 0 }}>
                      With <strong>15 music genres</strong> and thousands of album covers, the project evaluates how well visual information can distinguish between genres and where the model struggles when different genres share similar visual styles.
                    </p>
                  </div>
                </div>
              </div>

              {/* Why can the model get it wrong? */}
              <div className="card flex-col" style={{ 
                textAlign: 'left', 
                padding: 'var(--spacing-xxl)', 
                backgroundColor: 'var(--color-spring-meadow)',
                border: '1px solid var(--color-teal-waters)',
                borderRadius: '32px',
                boxShadow: 'none',
                marginTop: 'var(--spacing-xs)'
              }}>
                <h3 className="text-display" style={{ color: 'var(--color-teal-waters)', marginBottom: 'var(--spacing-md)', fontSize: '2rem', lineHeight: 1.2 }}>
                  Why can the model get it wrong?
                </h3>
                <div className="text-body" style={{ opacity: 0.9, lineHeight: 1.6, flexGrow: 1, margin: 0 }}>
                  <p style={{ margin: 0 }}>
                    Album covers from different genres can share similar colours, compositions, photography, typography, or artistic styles. When a cover doesn't strongly resemble the visual patterns learned from its genre, the model may classify it as another genre. These misclassifications are an important part of the research, showing the limits of using visual information alone.
                  </p>
                </div>
              </div>

              {/* Card 3 (Research Question) */}
              <div className="card flex-col flex-center" style={{ 
                backgroundColor: 'var(--color-teal-waters)', 
                color: 'var(--color-morning-mist)',
                padding: 'var(--spacing-xxl)', 
                textAlign: 'center',
                borderRadius: '32px',
                boxShadow: '0 16px 40px rgba(32, 70, 84, 0.15)',
                marginTop: 'var(--spacing-xs)'
              }}>
                <div className="text-small" style={{ textTransform: 'uppercase', letterSpacing: '2px', opacity: 0.7, marginBottom: 'var(--spacing-md)' }}>
                  Research Question
                </div>
                <blockquote className="text-h3" style={{ margin: 0, fontStyle: 'italic', lineHeight: 1.5, opacity: 0.95, color: 'var(--color-morning-mist)' }}>
                  "To what extent can album-cover colour and visual features be used to classify music genres and identify visually similar albums?"
                </blockquote>
              </div>

            </div>

            <div style={{ textAlign: 'center', maxWidth: '600px', margin: '0 auto var(--spacing-xl)', borderTop: '1px solid rgba(32, 70, 84, 0.1)', paddingTop: 'var(--spacing-xxl)' }}>
              <h2 className="text-display" style={{ marginBottom: 'var(--spacing-sm)' }}>How Playlify Works</h2>
              <p className="text-body-large" style={{ opacity: 0.8 }}>Can an album cover tell us something about its genre? Here is how our model sees it.</p>
            </div>

            <div className="flex-col gap-lg" style={{ maxWidth: '600px', margin: '0 auto', width: '100%' }}>
              {/* MobileNetV2 */}
              <div className="card flex-col flex-center" style={{ padding: 'var(--spacing-xl)', textAlign: 'center' }}>
                <h3 className="text-h2" style={{ color: 'var(--color-teal-waters)', marginBottom: 'var(--spacing-xs)' }}>1. MobileNetV2</h3>
                <p className="text-body-large" style={{ marginBottom: 'var(--spacing-xl)' }}>Turns the album cover into a rich visual representation.</p>
                <div className="flex-center flex-col gap-sm" style={{ opacity: 0.9, width: '100%' }}>
                  <div style={{ width: '240px', padding: '12px 16px', backgroundColor: 'var(--color-glacial-sky)', borderRadius: 'var(--radius-sm)' }}>ALBUM COVER</div>
                  <div style={{ fontSize: '1.2rem', color: 'var(--color-teal-waters)', opacity: 0.5 }}>↓</div>
                  <div style={{ width: '240px', padding: '12px 16px', backgroundColor: 'var(--color-glacial-sky)', borderRadius: 'var(--radius-sm)' }}>MobileNetV2</div>
                  <div style={{ fontSize: '1.2rem', color: 'var(--color-teal-waters)', opacity: 0.5 }}>↓</div>
                  <div style={{ width: '240px', padding: '12px 16px', backgroundColor: 'var(--color-spring-meadow)', borderRadius: 'var(--radius-sm)', fontWeight: 'bold', color: 'var(--color-teal-waters)' }}>1,280 visual features</div>
                </div>
              </div>

              <div style={{ textAlign: 'center', opacity: 0.5, fontSize: '1.5rem', color: 'var(--color-teal-waters)' }}>↓</div>

              {/* PCA */}
              <div className="card flex-col flex-center" style={{ padding: 'var(--spacing-xl)', textAlign: 'center' }}>
                <h3 className="text-h2" style={{ color: 'var(--color-teal-waters)', marginBottom: 'var(--spacing-xs)' }}>2. PCA</h3>
                <p className="text-body-large" style={{ marginBottom: 'var(--spacing-xl)' }}>Compresses the large feature representation into a smaller one to make the search easier and faster.</p>
                <div className="flex-center flex-col gap-sm" style={{ opacity: 0.9, width: '100%' }}>
                  <div style={{ width: '240px', padding: '12px 16px', backgroundColor: 'var(--color-glacial-sky)', borderRadius: 'var(--radius-sm)' }}>1,280 dimensions</div>
                  <div style={{ fontSize: '1.2rem', color: 'var(--color-teal-waters)', opacity: 0.5 }}>↓</div>
                  <div style={{ width: '240px', padding: '12px 16px', backgroundColor: 'var(--color-glacial-sky)', borderRadius: 'var(--radius-sm)' }}>PCA</div>
                  <div style={{ fontSize: '1.2rem', color: 'var(--color-teal-waters)', opacity: 0.5 }}>↓</div>
                  <div style={{ width: '240px', padding: '12px 16px', backgroundColor: 'var(--color-spring-meadow)', borderRadius: 'var(--radius-sm)', fontWeight: 'bold', color: 'var(--color-teal-waters)' }}>128 dimensions</div>
                </div>
              </div>

              <div style={{ textAlign: 'center', opacity: 0.5, fontSize: '1.5rem', color: 'var(--color-teal-waters)' }}>↓</div>

              {/* KNN */}
              <div className="card flex-col flex-center" style={{ padding: 'var(--spacing-xl)', textAlign: 'center' }}>
                <h3 className="text-h2" style={{ color: 'var(--color-teal-waters)', marginBottom: 'var(--spacing-xs)' }}>3. K-Nearest Neighbors (KNN)</h3>
                <p className="text-body-large" style={{ marginBottom: 'var(--spacing-xl)' }}>Looks for the albums closest to the uploaded cover.</p>
                <div className="flex-center flex-col gap-sm" style={{ opacity: 0.9, width: '100%' }}>
                  <div style={{ width: '240px', padding: '12px 16px', backgroundColor: 'var(--color-glacial-sky)', borderRadius: 'var(--radius-sm)' }}>NEW COVER</div>
                  <div style={{ fontSize: '1.2rem', color: 'var(--color-teal-waters)', opacity: 0.5 }}>↓</div>
                  <div style={{ width: '240px', padding: '12px 16px', backgroundColor: 'var(--color-glacial-sky)', borderRadius: 'var(--radius-sm)' }}>COMPARE WITH ALBUMS</div>
                  <div style={{ fontSize: '1.2rem', color: 'var(--color-teal-waters)', opacity: 0.5 }}>↓</div>
                  <div style={{ width: '240px', padding: '12px 16px', backgroundColor: 'var(--color-spring-meadow)', borderRadius: 'var(--radius-sm)', fontWeight: 'bold', color: 'var(--color-teal-waters)' }}>FIND CLOSEST NEIGHBOURS</div>
                </div>
              </div>
            </div>

            {/* Baselines and Comparison */}
            <div style={{ textAlign: 'center', maxWidth: '800px', margin: 'var(--spacing-xl) auto 0' }}>
              <h2 className="text-display" style={{ marginBottom: 'var(--spacing-md)' }}>How well did the different approaches perform?</h2>
              
              <div className="grid-2" style={{ textAlign: 'left', marginTop: 'var(--spacing-xl)', gap: 'var(--spacing-lg)' }}>
                <div className="panel-secondary flex-col gap-md">
                  <h4 className="text-h3" style={{ marginBottom: 'var(--spacing-xs)' }}>Research Baselines</h4>
                  <div>
                    <strong>MLP</strong>
                    <p className="text-small" style={{ opacity: 0.8, marginTop: '4px' }}>Tests whether a simpler neural network can classify genres from the extracted features.</p>
                  </div>
                  <div>
                    <strong>Logistic Regression</strong>
                    <p className="text-small" style={{ opacity: 0.8, marginTop: '4px' }}>Provides a basic linear benchmark for comparison.</p>
                  </div>
                </div>

                <div className="panel-dark flex-col gap-md">
                  <h4 className="text-h3" style={{ color: 'var(--color-spring-meadow)' }}>Performance</h4>
                  
                  <div>
                    <div className="flex-center" style={{ justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.875rem' }}>
                      <span>MobileNetV2 (Finetuned)</span>
                      <span>33.2%</span>
                    </div>
                    <div className="bar-chart-container bar-chart-container-light">
                      <div className="bar-chart-fill highlight" style={{ width: '33.2%', backgroundColor: 'var(--color-spring-meadow)' }}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex-center" style={{ justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.875rem' }}>
                      <span>MLP Neural Network</span>
                      <span>31.7%</span>
                    </div>
                    <div className="bar-chart-container bar-chart-container-light">
                      <div className="bar-chart-fill" style={{ width: '31.7%', backgroundColor: 'rgba(247, 249, 225, 0.4)' }}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex-center" style={{ justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.875rem' }}>
                      <span>Logistic Regression</span>
                      <span>20.0%</span>
                    </div>
                    <div className="bar-chart-container bar-chart-container-light">
                      <div className="bar-chart-fill" style={{ width: '20.0%', backgroundColor: 'rgba(247, 249, 225, 0.4)' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>


          </section>
        
        {/* New Visualizations Section */}
        <div id="model-reveals">
          <ResearchVisualizations />
        </div>
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
