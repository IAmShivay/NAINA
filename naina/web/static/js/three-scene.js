// naina/web/static/js/three-scene.js
import * as THREE from 'three';

let scene, camera, renderer, orb, innerOrb, voiceRing, ring2, ring3, particles;
let zoomLevel = 1.0;
let voiceActive = false;
const clock = new THREE.Clock();

function initScene() {
  const canvas = document.getElementById('three-canvas');
  if (!canvas) return;

  renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  renderer.setSize(window.innerWidth, window.innerHeight);

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.set(0, 0, 8);

  // Lighting
  scene.add(new THREE.AmbientLight(0x0D0A1E, 0.8));
  const p1 = new THREE.PointLight(0x7B6BB5, 3, 25);
  p1.position.set(5, 5, 5);
  scene.add(p1);
  const p2 = new THREE.PointLight(0xC4B5FD, 2, 20);
  p2.position.set(-4, -3, 4);
  scene.add(p2);
  const p3 = new THREE.PointLight(0x564A94, 1.5, 15);
  p3.position.set(0, 0, 6);
  scene.add(p3);

  // Outer wireframe sphere (large, dramatic)
  const outerGeo = new THREE.IcosahedronGeometry(3.5, 1);
  const outerOrb = new THREE.Mesh(outerGeo, new THREE.MeshBasicMaterial({
    color: 0x2D2060, wireframe: true, opacity: 0.12, transparent: true
  }));
  scene.add(outerOrb);

  // Central orb — wireframe icosahedron
  const orbGeo = new THREE.IcosahedronGeometry(1.5, 2);
  orb = new THREE.Mesh(orbGeo, new THREE.MeshBasicMaterial({
    color: 0x7B6BB5, wireframe: true, opacity: 0.8, transparent: true
  }));
  scene.add(orb);

  // Inner glowing core
  innerOrb = new THREE.Mesh(
    new THREE.IcosahedronGeometry(0.7, 2),
    new THREE.MeshPhongMaterial({
      color: 0x564A94, emissive: 0x3D3580, emissiveIntensity: 1.2,
      transparent: true, opacity: 0.9
    })
  );
  scene.add(innerOrb);

  // Solid core center
  const solidCore = new THREE.Mesh(
    new THREE.SphereGeometry(0.25, 16, 16),
    new THREE.MeshPhongMaterial({ color: 0xC4B5FD, emissive: 0x9C8FD4, emissiveIntensity: 2 })
  );
  scene.add(solidCore);

  // Voice ring (equatorial)
  voiceRing = new THREE.Mesh(
    new THREE.RingGeometry(1.9, 2.05, 80),
    new THREE.MeshBasicMaterial({ color: 0x7B6BB5, side: THREE.DoubleSide, transparent: true, opacity: 0.5 })
  );
  scene.add(voiceRing);

  // Second ring — tilted 60deg
  ring2 = new THREE.Mesh(
    new THREE.RingGeometry(2.4, 2.5, 80),
    new THREE.MeshBasicMaterial({ color: 0x564A94, side: THREE.DoubleSide, transparent: true, opacity: 0.3 })
  );
  ring2.rotation.x = Math.PI / 3;
  scene.add(ring2);

  // Third ring — tilted opposite
  ring3 = new THREE.Mesh(
    new THREE.RingGeometry(2.8, 2.88, 80),
    new THREE.MeshBasicMaterial({ color: 0x9C8FD4, side: THREE.DoubleSide, transparent: true, opacity: 0.18 })
  );
  ring3.rotation.x = -Math.PI / 4;
  ring3.rotation.y = Math.PI / 5;
  scene.add(ring3);

  // Particle field — 800 particles (was 2000), larger size for visibility
  const count = 800;
  const pos = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    pos[i*3]   = (Math.random() - 0.5) * 35;
    pos[i*3+1] = (Math.random() - 0.5) * 35;
    pos[i*3+2] = (Math.random() - 0.5) * 35 - 5;
    // Slight color variation between purple and lavender
    const bright = 0.4 + Math.random() * 0.6;
    colors[i*3]   = 0.34 * bright;  // R
    colors[i*3+1] = 0.29 * bright;  // G
    colors[i*3+2] = 0.58 * bright;  // B
  }
  const pGeo = new THREE.BufferGeometry();
  pGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  pGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  particles = new THREE.Points(pGeo, new THREE.PointsMaterial({
    size: 0.07, vertexColors: true, transparent: true, opacity: 0.85
  }));
  scene.add(particles);

  // Grid backdrop — fewer subdivisions for perf
  const grid = new THREE.Mesh(
    new THREE.PlaneGeometry(30, 22, 12, 8),
    new THREE.MeshBasicMaterial({ color: 0x1A1060, wireframe: true, transparent: true, opacity: 0.12 })
  );
  grid.position.z = -10;
  scene.add(grid);

  // Horizon grid (floor)
  const floorGrid = new THREE.Mesh(
    new THREE.PlaneGeometry(40, 40, 16, 16),
    new THREE.MeshBasicMaterial({ color: 0x2D2060, wireframe: true, transparent: true, opacity: 0.1 })
  );
  floorGrid.rotation.x = -Math.PI / 2.4;
  floorGrid.position.y = -5;
  scene.add(floorGrid);

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  animate();
}

function animate() {
  requestAnimationFrame(animate);
  const t = clock.getElapsedTime();

  if (orb) {
    orb.rotation.x = t * 0.25;
    orb.rotation.y = t * 0.4;
  }
  if (innerOrb) {
    innerOrb.rotation.x = -t * 0.3;
    innerOrb.rotation.y = t * 0.6;
  }
  if (voiceRing) {
    const pulse = voiceActive ? 1 + Math.sin(t * 8) * 0.08 : 1 + Math.sin(t * 1.5) * 0.03;
    voiceRing.scale.set(pulse, pulse, 1);
    voiceRing.rotation.z = t * 0.25;
  }
  if (ring2) ring2.rotation.z = -t * 0.15;
  if (ring3) ring3.rotation.x = -Math.PI / 4 + Math.sin(t * 0.4) * 0.1;

  if (particles) {
    particles.rotation.y = t * 0.008;
    particles.rotation.x = t * 0.003;
  }

  if (camera) {
    camera.position.y = Math.sin(t * 0.25) * 0.3;
    camera.position.x = Math.cos(t * 0.18) * 0.2;
    camera.lookAt(0, 0, 0);
  }

  if (renderer && scene && camera) renderer.render(scene, camera);
}

export function setVoiceActive(active) {
  voiceActive = active;
  if (!voiceRing) return;
  voiceRing.material.opacity = active ? 0.9 : 0.5;
  voiceRing.material.color.setHex(active ? 0xC4B5FD : 0x7B6BB5);
  if (orb) orb.material.color.setHex(active ? 0xC4B5FD : 0x7B6BB5);
}

export function zoomIn() {
  zoomLevel = Math.min(zoomLevel + 0.15, 2.5);
  if (camera) camera.position.z = 8 / zoomLevel;
}

export function zoomOut() {
  zoomLevel = Math.max(zoomLevel - 0.15, 0.5);
  if (camera) camera.position.z = 8 / zoomLevel;
}

initScene();
window.__nainaScene = { setVoiceActive, zoomIn, zoomOut };
