import numpy as np
import math
# Based on Pseudocode implementation written by David Eberly
# From: https://www.geometrictools.com/Documentation/LeastSquaresFitting.pdf
# Shared under the following license: https://creativecommons.org/licenses/by/4.0/
# Implemented and modified for Blender/Python by Pasha van Bijlert

def preprocess(n, points):
    average = np.zeros(3)
    for point in points:
        average += point
    average /= n

    X = points - average
    
    products = np.zeros((n, 6))

    for i in range(n):
       
        products[i][0] = X[i][0] * X[i][0]
        products[i][1] = X[i][0] * X[i][1]
        products[i][2] = X[i][0] * X[i][2]
        products[i][3] = X[i][1] * X[i][1]
        products[i][4] = X[i][1] * X[i][2]
        products[i][5] = X[i][2] * X[i][2]

    mu = np.zeros(6)
    
    for i in range(n):
        mu[0] += products[i][0]
        mu[1] += 2 * products[i][1]
        mu[2] += 2 * products[i][2]
        mu[3] += products[i][3]
        mu[4] += 2 * products[i][4]
        mu[5] += products[i][5]

    mu /= n

    F0 = np.zeros((3, 3))
    F1 = np.zeros((3, 6))
    F2 = np.zeros((6, 6))

    for i in range(n):
        delta = np.zeros(6)*np.nan
        delta[0] = products[i][0] - mu[0]
        delta[1] = 2*products[i][1] - mu[1]
        delta[2] = 2*products[i][2] - mu[2]
        delta[3] = products[i][3] - mu[3]
        delta[4] = 2*products[i][4] - mu[4]
        delta[5] = products[i][5] - mu[5]
        
        
        F0[0, 0] += products[i][0]
        F0[0, 1] += products[i][1]
        F0[0, 2] += products[i][2]
        F0[1, 1] += products[i][3]
        F0[1, 2] += products[i][4]
        F0[2, 2] += products[i][5]

        F1 += np.outer(X[i], delta)
        F2 += np.outer(delta, delta)

    F0 /= n
    F0[1, 0] = F0[0, 1]
    F0[2, 0] = F0[0, 2]
    F0[2, 1] = F0[1, 2]
    F1 /= n
    F2 /= n

    return average, mu, F0, F1, F2

def G(n, X, mu, F0, F1, F2, W):
    P = np.eye(3) - np.outer(W, W)
    S = np.array([[0, -W[2], W[1]], 
                  [W[2], 0, -W[0]], 
                  [-W[1], W[0], 0]])

    A = P @ F0 @ P
    hatA = -S @ A @ S
    hatAA = hatA @ A
    trace = np.trace(hatAA)
    Q = hatA / trace

    p = np.array([P[0, 0], P[0, 1], P[0, 2], P[1, 1], P[1, 2], P[2, 2]])
    alpha = F1 @ p
    beta = Q @ alpha

    error = (np.dot(p, F2 @ p) - 4 * np.dot(alpha, beta) + 4 * np.dot(beta, F0 @ beta)) / n
    PC = beta
    rSqr = np.dot(p, mu) + np.dot(beta, beta)

    return error, PC, rSqr

def fit_cylinder(n, points, imax=200, jmax=200):
    average, mu, F0, F1, F2 = preprocess(n, points)
    X = points - average

    minError = float('inf')
    W = np.zeros(3)
    C = np.zeros(3)
    rSqr = 0

    halfPi = np.pi / 2
    twoPi = 2 * np.pi

    for j in range(jmax + 1):
        phi = halfPi * j / jmax
        csphi = math.cos(phi)
        snphi = math.sin(phi)
        
        for i in range(imax+1):
            theta = twoPi * i / imax
            cstheta = math.cos(theta)
            sntheta = math.sin(theta)
            currentW = np.array([cstheta * snphi, sntheta * snphi, csphi])
            error, currentC, currentRSqr = G(n, X, mu, F0, F1, F2, currentW)

            if error < minError:
                minError = error
                W = currentW
                C = currentC
                rSqr = currentRSqr

    C += average
    return minError, C, W, rSqr