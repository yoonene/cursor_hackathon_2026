import React from 'react'

interface FateMeLogoProps {
  width?: number
  /** When true, the SVG fills its container via CSS (width/height 100%) */
  fullScreen?: boolean
  accentColor?: string
  starLineColor?: string
  textColor?: string
  showTagline?: boolean
  showConstellations?: boolean
  className?: string
}

const GOOGLE_FONTS_URL =
  'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300&family=Raleway:wght@200;300&display=swap'

const FateMeLogo: React.FC<FateMeLogoProps> = ({
  width = 400,
  fullScreen = false,
  accentColor = '#7A9E89',
  starLineColor = '#B2C9BB',
  textColor = '#1a1a1a',
  showTagline = true,
  showConstellations = true,
  className,
}) => {
  const viewBoxWidth = 680
  const viewBoxHeight = 360
  const height = (width / viewBoxWidth) * viewBoxHeight

  const leftStars = [
    { cx: 68, cy: 95, r: 1.5, opacity: 0.7 },
    { cx: 98, cy: 72, r: 1, opacity: 0.5 },
    { cx: 115, cy: 108, r: 2, opacity: 0.8 },
    { cx: 88, cy: 130, r: 1, opacity: 0.4 },
    { cx: 52, cy: 140, r: 1.5, opacity: 0.6 },
    { cx: 132, cy: 88, r: 1, opacity: 0.5 },
    { cx: 78, cy: 62, r: 1, opacity: 0.4 },
  ]

  const leftLines: [number, number, number, number][] = [
    [68, 95, 98, 72],
    [98, 72, 115, 108],
    [115, 108, 88, 130],
    [88, 130, 52, 140],
    [68, 95, 52, 140],
    [98, 72, 132, 88],
    [78, 62, 98, 72],
  ]

  const rightStars = [
    { cx: 565, cy: 88, r: 1.5, opacity: 0.6 },
    { cx: 590, cy: 112, r: 1, opacity: 0.5 },
    { cx: 612, cy: 75, r: 2, opacity: 0.7 },
    { cx: 598, cy: 138, r: 1, opacity: 0.4 },
    { cx: 572, cy: 120, r: 1.5, opacity: 0.5 },
    { cx: 620, cy: 108, r: 1, opacity: 0.6 },
    { cx: 635, cy: 88, r: 1, opacity: 0.4 },
  ]

  const rightLines: [number, number, number, number][] = [
    [565, 88, 590, 112],
    [590, 112, 572, 120],
    [590, 112, 598, 138],
    [612, 75, 590, 112],
    [612, 75, 635, 88],
    [635, 88, 620, 108],
  ]

  return (
    <>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link href={GOOGLE_FONTS_URL} rel="stylesheet" />

      <svg
        {...(fullScreen
          ? { width: '100%', height: '100%' }
          : { width, height })}
        viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="Fate.me logo"
        xmlns="http://www.w3.org/2000/svg"
        className={className}
      >
        <title>Fate.me</title>
        <desc>Fate.me saju service logo</desc>

        {showConstellations && (
          <g>
            {/* Left constellation */}
            {leftLines.map(([x1, y1, x2, y2], i) => (
              <line
                key={`left-line-${i}`}
                x1={x1} y1={y1} x2={x2} y2={y2}
                stroke={starLineColor}
                strokeWidth={0.5}
                opacity={0.6}
              />
            ))}
            {leftStars.map((star, i) => (
              <circle
                key={`left-star-${i}`}
                cx={star.cx}
                cy={star.cy}
                r={star.r}
                fill={accentColor}
                opacity={star.opacity}
              />
            ))}

            {/* Right constellation */}
            {rightLines.map(([x1, y1, x2, y2], i) => (
              <line
                key={`right-line-${i}`}
                x1={x1} y1={y1} x2={x2} y2={y2}
                stroke={starLineColor}
                strokeWidth={0.5}
                opacity={0.6}
              />
            ))}
            {rightStars.map((star, i) => (
              <circle
                key={`right-star-${i}`}
                cx={star.cx}
                cy={star.cy}
                r={star.r}
                fill={accentColor}
                opacity={star.opacity}
              />
            ))}
          </g>
        )}

        {/* Main logo text */}
        <text x={340} y={200} textAnchor="middle">
          {/* "Fate" — upright */}
          <tspan
            fontFamily="'Cormorant Garamond', Georgia, serif"
            fontWeight={300}
            fontSize={88}
            fill={textColor}
            letterSpacing={-2}
          >
            Fate
          </tspan>
          {/* "." — accent color */}
          <tspan
            fontFamily="'Cormorant Garamond', Georgia, serif"
            fontWeight={400}
            fontSize={88}
            fill={accentColor}
          >
            .
          </tspan>
          {/* "me" — italic + accent color */}
          <tspan
            fontFamily="'Cormorant Garamond', Georgia, serif"
            fontStyle="italic"
            fontWeight={300}
            fontSize={88}
            fill={accentColor}
            letterSpacing={-1}
          >
            me
          </tspan>
        </text>

        {/* Divider */}
        {showTagline && (
          <line
            x1={240} y1={228}
            x2={440} y2={228}
            stroke={starLineColor}
            strokeWidth={0.5}
            opacity={0.8}
          />
        )}

        {/* Tagline */}
        {showTagline && (
          <text
            x={340}
            y={252}
            textAnchor="middle"
            fontFamily="'Raleway', 'Helvetica Neue', sans-serif"
            fontWeight={200}
            fontSize={11}
            fill="#999999"
            letterSpacing={5}
          >
            YOUR DESTINY, DECODED
          </text>
        )}

        {/* Bottom star decoration */}
        {showConstellations && (
          <g>
            <circle cx={340} cy={282} r={1.5} fill={accentColor} opacity={0.5} />
            <circle cx={326} cy={287} r={1} fill={accentColor} opacity={0.3} />
            <circle cx={354} cy={287} r={1} fill={accentColor} opacity={0.3} />
            <line x1={326} y1={287} x2={340} y2={282} stroke={starLineColor} strokeWidth={0.4} opacity={0.5} />
            <line x1={354} y1={287} x2={340} y2={282} stroke={starLineColor} strokeWidth={0.4} opacity={0.5} />
          </g>
        )}
      </svg>
    </>
  )
}

export default FateMeLogo
