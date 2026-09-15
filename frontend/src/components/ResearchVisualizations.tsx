import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { Info, ZoomIn } from 'lucide-react';

import pcaDataJson from '../data/pca_data.json';
import profilesJson from '../data/genre_profiles.json';
import matrixDataJson from '../data/confusion_matrix.json';

interface PCAData {
  id: string;
  genre: string;
  x: number;
  y: number;
  image_url: string;
}

interface ProfileData {
  genre: string;
  sample_size: number;
  r_mean: number;
  g_mean: number;
  b_mean: number;
  brightness: number;
  contrast: number;
}

interface MatrixData {
  accuracy: number;
  macro_f1: number;
  weighted_f1: number;
  genres: string[];
  matrix: number[][];
}

const ResearchVisualizations: React.FC = () => {
  const pcaData: PCAData[] = pcaDataJson as PCAData[];
  const profiles: ProfileData[] = profilesJson as ProfileData[];
  const matrixData: MatrixData = matrixDataJson as MatrixData;

  const [activeGenre, setActiveGenre] = useState<string | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<PCAData | null>(null);
  const [hoveredCell, setHoveredCell] = useState<{true_label: string, pred_label: string, count: number, total: number} | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  if (!matrixData || profiles.length === 0 || pcaData.length === 0) {
    return <div className="section" style={{ textAlign: 'center', opacity: 0.5 }}>Loading research visualizations...</div>;
  }

  // --- PCA Plot Helpers ---
  // Normalize X and Y to fit in 0-100% SVG coordinates
  const allX = pcaData.map(d => d.x);
  const allY = pcaData.map(d => d.y);
  const minX = Math.min(...allX) - 0.5;
  const maxX = Math.max(...allX) + 0.5;
  const minY = Math.min(...allY) - 0.5;
  const maxY = Math.max(...allY) + 0.5;

  // --- Matrix Helpers ---
  const maxMatrixVal = Math.max(...matrixData.matrix.flat());

  return (
    <section className="section flex-col animate-fade-in" style={{
      padding: 'var(--spacing-xxl)',
      marginTop: 'var(--spacing-xl)',
      backgroundColor: 'var(--color-morning-mist)',
      borderTop: '1px solid rgba(32, 70, 84, 0.1)'
    }}>
      <div style={{ textAlign: 'center', maxWidth: '800px', margin: '0 auto var(--spacing-xxl)' }}>
        <h2 className="text-display" style={{ marginBottom: 'var(--spacing-sm)' }}>WHAT THE MODEL REVEALS</h2>
        <p className="text-body-large" style={{ opacity: 0.8 }}>
          Explore how album artwork behaves as visual data — from feature space and genre separation to the patterns behind model predictions.
        </p>
      </div>

      {/* 01 - VISUAL FEATURE SPACE */}
      <div className="card flex-col gap-lg" style={{ marginBottom: 'var(--spacing-xxl)' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--spacing-md)', borderBottom: '1px solid rgba(32, 70, 84, 0.1)', paddingBottom: 'var(--spacing-md)' }}>
          <div>
            <span className="text-small" style={{ opacity: 0.5, letterSpacing: '2px' }}>01 / 03</span>
            <h3 className="text-h3" style={{ margin: 0 }}>Visual Feature Space</h3>
          </div>
          <p className="text-body" style={{ maxWidth: '400px', margin: 0, opacity: 0.8, minWidth: '250px', flex: '1 1 auto' }}>
            MobileNetV2 converts each album cover into a high-dimensional visual feature representation. PCA reduces these features to two dimensions so we can explore how albums are positioned and clustered based on visual similarity.
          </p>
        </div>

        <div className="grid-2" style={{ gap: 'var(--spacing-lg)' }}>
          {/* Plot */}
          <div style={{ position: 'relative', width: '100%', aspectRatio: '1/1', backgroundColor: 'rgba(32, 70, 84, 0.02)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(32, 70, 84, 0.05)', overflow: 'hidden' }}>
            <svg width="100%" height="100%" style={{ overflow: 'visible' }}>
              {pcaData.map((d, i) => {
                const normX = ((d.x - minX) / (maxX - minX)) * 100;
                const normY = ((d.y - minY) / (maxY - minY)) * 100;
                const isFaded = activeGenre && activeGenre !== d.genre;
                
                return (
                  <circle
                    key={i}
                    cx={`${normX}%`}
                    cy={`${normY}%`}
                    r={hoveredPoint === d ? 6 : 3}
                    fill={isFaded ? 'rgba(32, 70, 84, 0.1)' : 'var(--color-teal-waters)'}
                    opacity={isFaded ? 0.3 : 0.8}
                    style={{ transition: 'all 0.2s ease', cursor: 'pointer' }}
                    onMouseEnter={() => setHoveredPoint(d)}
                    onMouseLeave={() => setHoveredPoint(null)}
                  />
                );
              })}
            </svg>
            
            {/* Tooltip */}
            {hoveredPoint && (
              <div style={{
                position: 'absolute',
                top: `${((hoveredPoint.y - minY) / (maxY - minY)) * 100}%`,
                left: `${((hoveredPoint.x - minX) / (maxX - minX)) * 100}%`,
                transform: 'translate(-50%, -120%)',
                backgroundColor: 'var(--color-teal-waters)',
                color: 'var(--color-morning-mist)',
                padding: 'var(--spacing-sm)',
                borderRadius: 'var(--radius-sm)',
                pointerEvents: 'none',
                display: 'flex',
                gap: 'var(--spacing-sm)',
                alignItems: 'center',
                boxShadow: 'var(--shadow-hover)',
                zIndex: 10
              }}>
                <div style={{ width: '40px', height: '40px', backgroundColor: 'var(--color-glacial-sky)', overflow: 'hidden', borderRadius: '4px' }}>
                   {hoveredPoint.image_url && <img src={hoveredPoint.image_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />}
                </div>
                <div className="flex-col">
                  <strong className="text-small">{hoveredPoint.genre}</strong>
                  <span style={{ fontSize: '0.75rem', opacity: 0.7 }}>PCA Data Point</span>
                </div>
              </div>
            )}
          </div>
          
          {/* Controls & Insight */}
          <div className="flex-col gap-lg" style={{ justifyContent: 'center' }}>
            <div>
               <h4 className="text-body-large" style={{ marginBottom: 'var(--spacing-md)' }}>Filter by Genre</h4>
               <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--spacing-sm)' }}>
                 {matrixData.genres.map(g => (
                   <button 
                     key={g} 
                     onClick={() => setActiveGenre(activeGenre === g ? null : g)}
                     style={{ 
                       padding: '4px 12px', 
                       borderRadius: 'var(--radius-xl)', 
                       border: `1px solid ${activeGenre === g ? 'var(--color-teal-waters)' : 'rgba(32, 70, 84, 0.2)'}`,
                       backgroundColor: activeGenre === g ? 'var(--color-teal-waters)' : 'transparent',
                       color: activeGenre === g ? 'var(--color-morning-mist)' : 'var(--color-teal-waters)',
                       cursor: 'pointer',
                       fontSize: '0.875rem',
                       transition: 'all 0.2s ease'
                     }}
                   >
                     {g}
                   </button>
                 ))}
               </div>
            </div>

            <div className="panel-secondary" style={{ padding: 'var(--spacing-md)' }}>
              <p className="text-small" style={{ textTransform: 'uppercase', letterSpacing: '1px', opacity: 0.7, marginBottom: 'var(--spacing-xs)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Info size={14} /> Research Insight
              </p>
              <p className="text-body" style={{ margin: 0 }}>
                Several genres occupy overlapping regions of visual feature space, suggesting that visual similarity does not always correspond to musical genre. This helps us investigate whether albums from the same genre form distinguishable visual patterns.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 02 - GENRE CONFUSION EXPLORER */}
      <div className="card flex-col gap-lg" style={{ marginBottom: 'var(--spacing-xxl)' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--spacing-md)', borderBottom: '1px solid rgba(32, 70, 84, 0.1)', paddingBottom: 'var(--spacing-md)' }}>
          <div>
            <span className="text-small" style={{ opacity: 0.5, letterSpacing: '2px' }}>02 / 03</span>
            <h3 className="text-h3" style={{ margin: 0 }}>Where Does the Model Get Confused?</h3>
          </div>
          <p className="text-body" style={{ maxWidth: '400px', margin: 0, opacity: 0.8, minWidth: '250px', flex: '1 1 auto' }}>
            The confusion matrix compares the model's predicted genre with the actual genre on the test set, showing where classifications are correct and where genres are commonly confused. Examining the confusion matrix helps identify which genres are easier or harder for the model to distinguish.
          </p>
        </div>

        <div className="flex-col gap-lg">
          <div 
            style={{ position: 'relative', overflowX: 'auto', paddingBottom: 'var(--spacing-lg)' }}
            onMouseMove={(e) => setMousePos({ x: e.clientX, y: e.clientY })}
          >
             <div style={{ display: 'grid', gridTemplateColumns: `100px repeat(${matrixData.genres.length}, minmax(30px, 1fr))`, gap: '2px', width: '100%', minWidth: '600px' }}>
                {/* Headers */}
                <div className="text-small" style={{ textAlign: 'right', paddingRight: 'var(--spacing-sm)', display: 'flex', alignItems: 'flex-end', justifyContent: 'flex-end', opacity: 0.5 }}>Actual \ Pred</div>
                {matrixData.genres.map((g, i) => (
                  <div key={i} className="text-small" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)', textAlign: 'left', opacity: 0.7, paddingBottom: '4px' }}>
                    {g.substring(0, 4)}.
                  </div>
                ))}
                
                {/* Rows */}
                {matrixData.matrix.map((row, i) => {
                  const trueLabel = matrixData.genres[i];
                  const rowTotal = row.reduce((a, b) => a + b, 0);
                  
                  return (
                    <React.Fragment key={i}>
                      <div className="text-small flex-center" style={{ justifyContent: 'flex-end', paddingRight: 'var(--spacing-sm)', opacity: 0.7 }}>
                        {trueLabel}
                      </div>
                      {row.map((val, j) => {
                        const predLabel = matrixData.genres[j];
                        const isCorrect = i === j;
                        const opacity = val === 0 ? 0.02 : Math.max(0.05, Math.min(1, val / maxMatrixVal * 2));
                        
                        return (
                          <div 
                            key={`${i}-${j}`}
                            onMouseEnter={() => setHoveredCell({true_label: trueLabel, pred_label: predLabel, count: val, total: rowTotal})}
                            onMouseLeave={() => setHoveredCell(null)}
                            style={{ 
                              aspectRatio: '1/1', 
                              backgroundColor: isCorrect ? 'var(--color-spring-meadow)' : 'var(--color-teal-waters)',
                              opacity: isCorrect ? Math.max(0.1, opacity * 1.5) : opacity,
                              borderRadius: '2px',
                              cursor: 'pointer',
                              border: hoveredCell?.true_label === trueLabel && hoveredCell?.pred_label === predLabel ? '2px solid var(--color-teal-waters)' : 'none'
                            }}
                          />
                        );
                      })}
                    </React.Fragment>
                  );
                })}
             </div>
             
             {hoveredCell && createPortal(
               <div className="panel-dark flex-col" style={{ 
                 position: 'fixed', 
                 top: mousePos.y + 15, 
                 left: mousePos.x + 15, 
                 padding: 'var(--spacing-md)', 
                 borderRadius: 'var(--radius-sm)', 
                 minWidth: '200px', 
                 pointerEvents: 'none', 

                 boxShadow: 'var(--shadow-hover)',
                 zIndex: 100
               }}>
                 <div className="text-small" style={{ opacity: 0.7 }}>Actual: <strong>{hoveredCell.true_label}</strong></div>
                 <div className="text-small" style={{ opacity: 0.7 }}>Predicted: <strong>{hoveredCell.pred_label}</strong></div>
                 <div style={{ marginTop: 'var(--spacing-xs)' }}>
                   <strong style={{ fontSize: '1.2rem', color: 'var(--color-spring-meadow)' }}>{hoveredCell.count}</strong> samples 
                   <span style={{ opacity: 0.7, fontSize: '0.8rem', marginLeft: '8px' }}>({hoveredCell.total > 0 ? ((hoveredCell.count/hoveredCell.total)*100).toFixed(1) : 0}%)</span>
                 </div>
               </div>,
               document.body
             )}
          </div>
          
          <div className="grid-2" style={{ alignItems: 'start', gap: 'var(--spacing-xl)' }}>
            <div className="panel-dark flex-center" style={{ justifyContent: 'space-around', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-sm)' }}>
               <div style={{ textAlign: 'center' }}>
                 <div className="text-small" style={{ opacity: 0.7, textTransform: 'uppercase' }}>Overall Accuracy</div>
                 <div className="text-h3" style={{ color: 'var(--color-spring-meadow)', margin: 0 }}>{(matrixData.accuracy * 100).toFixed(2)}%</div>
               </div>
               <div style={{ textAlign: 'center' }}>
                 <div className="text-small" style={{ opacity: 0.7, textTransform: 'uppercase' }}>Macro F1</div>
                 <div className="text-h3" style={{ color: 'var(--color-morning-mist)', margin: 0 }}>{matrixData.macro_f1.toFixed(4)}</div>
               </div>
               <div style={{ textAlign: 'center' }}>
                 <div className="text-small" style={{ opacity: 0.7, textTransform: 'uppercase' }}>Weighted F1</div>
                 <div className="text-h3" style={{ color: 'var(--color-morning-mist)', margin: 0 }}>{matrixData.weighted_f1.toFixed(4)}</div>
               </div>
            </div>
            
            <div className="panel-secondary" style={{ padding: 'var(--spacing-md)', margin: 0 }}>
              <p className="text-small" style={{ textTransform: 'uppercase', letterSpacing: '1px', opacity: 0.7, marginBottom: 'var(--spacing-xs)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Info size={14} /> Research Insight
              </p>
              <p className="text-body" style={{ margin: 0 }}>
                Some genres are frequently confused with others (like Rock and Metal, or Electronic and Pop), indicating that their album artwork occupies similar visual territory. The model's errors are useful research evidence: they show where visual information alone becomes insufficient for reliable genre separation.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 03 - VISUAL DNA OF GENRES */}
      <div className="card flex-col gap-lg">
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--spacing-md)', borderBottom: '1px solid rgba(32, 70, 84, 0.1)', paddingBottom: 'var(--spacing-md)' }}>
          <div>
            <span className="text-small" style={{ opacity: 0.5, letterSpacing: '2px' }}>03 / 03</span>
            <h3 className="text-h3" style={{ margin: 0 }}>Visual DNA of Each Genre</h3>
          </div>
          <p className="text-body" style={{ maxWidth: '400px', margin: 0, opacity: 0.8, minWidth: '250px', flex: '1 1 auto' }}>
            Explore whether different music genres show recurring visual characteristics across their album artwork. This connects the visual analysis back to the research question by examining whether measurable visual patterns are associated with different genres.
          </p>
        </div>

        <div className="grid-2" style={{ gap: 'var(--spacing-xl)' }}>
          <div className="flex-col gap-sm">
            {profiles.map(p => (
              <div 
                key={p.genre} 
                className={`flex-center ${activeGenre === p.genre ? 'panel-dark' : ''}`}
                style={{ 
                  justifyContent: 'space-between', 
                  padding: '8px 12px', 
                  borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer',
                  border: activeGenre === p.genre ? 'none' : '1px solid rgba(32, 70, 84, 0.1)',
                  transition: 'all 0.2s ease'
                }}
                onClick={() => setActiveGenre(p.genre)}
              >
                <span style={{ fontWeight: activeGenre === p.genre ? 600 : 400 }}>{p.genre}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="text-small" style={{ opacity: 0.6 }}>{p.sample_size} samples</span>
                  <div style={{ 
                    width: '32px', 
                    height: '16px', 
                    borderRadius: '2px', 
                    backgroundColor: `rgb(${p.r_mean}, ${p.g_mean}, ${p.b_mean})`,
                    border: '1px solid rgba(0,0,0,0.1)'
                  }}></div>
                </div>
              </div>
            ))}
          </div>
          
          <div>
            {activeGenre ? (() => {
              const profile = profiles.find(p => p.genre === activeGenre);
              if (!profile) return null;
              
              return (
                <div className="panel-secondary flex-col gap-lg" style={{ position: 'sticky', top: '24px' }}>
                  <div>
                    <div className="text-small" style={{ textTransform: 'uppercase', letterSpacing: '1px', opacity: 0.7 }}>Genre Profile</div>
                    <h3 className="text-display" style={{ margin: 0, color: 'var(--color-teal-waters)' }}>{profile.genre}</h3>
                  </div>
                  
                  <div className="flex-col gap-md">
                    <div>
                      <div className="flex-center" style={{ justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.875rem' }}>
                        <span>Dominant RGB Average</span>
                        <span>rgb({Math.round(profile.r_mean)}, {Math.round(profile.g_mean)}, {Math.round(profile.b_mean)})</span>
                      </div>
                      <div style={{ width: '100%', height: '48px', borderRadius: 'var(--radius-sm)', backgroundColor: `rgb(${profile.r_mean}, ${profile.g_mean}, ${profile.b_mean})`, border: '1px solid rgba(32, 70, 84, 0.1)' }}></div>
                    </div>
                    
                    <div className="grid-2" style={{ gap: 'var(--spacing-md)' }}>
                      <div>
                        <div className="flex-center" style={{ justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.875rem' }}>
                          <span>Brightness</span>
                          <span>{profile.brightness.toFixed(1)}</span>
                        </div>
                        <div className="bar-chart-container" style={{ backgroundColor: 'rgba(32, 70, 84, 0.1)' }}>
                           <div className="bar-chart-fill" style={{ width: `${(profile.brightness / 255) * 100}%` }}></div>
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex-center" style={{ justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.875rem' }}>
                          <span>Contrast (Variance)</span>
                          <span>{profile.contrast.toFixed(1)}</span>
                        </div>
                        <div className="bar-chart-container" style={{ backgroundColor: 'rgba(32, 70, 84, 0.1)' }}>
                           <div className="bar-chart-fill" style={{ width: `${(profile.contrast / 128) * 100}%`, backgroundColor: 'var(--color-teal-waters)' }}></div>
                        </div>
                      </div>
                    </div>
                    
                    <div style={{ padding: 'var(--spacing-md)', backgroundColor: 'rgba(255, 255, 255, 0.5)', borderRadius: 'var(--radius-sm)', marginTop: 'var(--spacing-sm)' }}>
                      <p className="text-small" style={{ margin: 0, opacity: 0.8 }}>
                        Based on the dataset of <strong>{profile.sample_size}</strong> album covers. 
                        The metrics display the average colour distribution and brightness/contrast extracted via HSV and RGB channels prior to MobileNetV2 feature extraction.
                      </p>
                    </div>
                  </div>
                </div>
              );
            })() : (
              <div className="flex-center flex-col gap-md" style={{ height: '100%', minHeight: '300px', backgroundColor: 'rgba(32, 70, 84, 0.02)', borderRadius: 'var(--radius-lg)', border: '1px dashed rgba(32, 70, 84, 0.2)' }}>
                <ZoomIn size={32} style={{ opacity: 0.3 }} />
                <p className="text-body" style={{ opacity: 0.5 }}>Select a genre to view its visual profile.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};

export default ResearchVisualizations;
